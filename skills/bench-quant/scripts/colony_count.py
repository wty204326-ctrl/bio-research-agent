#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""克隆形成（集落）计数：平板图像 → 自动计数 + 尺寸分布 + 标注图
用法: python colony_count.py --img plate.png [--min-area 30] [--max-area 8000] [--invert] --out-dir out
原理: 灰度→模糊→Otsu（默认暗集落亮背景；--invert 反转）→形态学开运算→轮廓面积过滤
输出: colonies.csv（编号/坐标/面积/等效直径）/ summary.csv / overlay.png（白底红线标注）
"""
import argparse, os
import numpy as np
import cv2
import pandas as pd

def main(a):
    os.makedirs(a.out_dir, exist_ok=True)
    bgr = cv2.imread(a.img, cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f"读不到图: {a.img}")
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    thr, _ = cv2.threshold(blur, 0, 255, cv2.THRESH_OTSU)
    # 亮背景→集落在暗侧；暗背景→亮侧；--invert 强制反转
    frac_dark = (blur < thr).mean()
    mask = (blur > thr) if a.invert else ((blur < thr) if frac_dark < 0.5 else (blur > thr))
    m = mask.astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel, iterations=2)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rows = []
    for c in cnts:
        area = cv2.contourArea(c)
        if not (a.min_area <= area <= a.max_area):
            continue
        M = cv2.moments(c)
        if M["m00"] == 0:
            continue
        rows.append(dict(colony=len(rows) + 1,
                         cx=round(M["m10"] / M["m00"], 1), cy=round(M["m01"] / M["m00"], 1),
                         area_px=int(area), equiv_diam_px=round(2 * np.sqrt(area / np.pi), 1)))
    df = pd.DataFrame(rows)
    overlay = bgr.copy()
    for _, r in df.iterrows():
        cv2.circle(overlay, (int(r["cx"]), int(r["cy"])), int(r["equiv_diam_px"] / 2) + 4, (0, 0, 255), 2)
        cv2.putText(overlay, str(int(r["colony"])), (int(r["cx"]) - 6, int(r["cy"]) - int(r["equiv_diam_px"] / 2) - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(a.out_dir, "overlay.png"), overlay)
    if len(df):
        df.to_csv(os.path.join(a.out_dir, "colonies.csv"), index=False, encoding="utf-8-sig")
        sizes = df["area_px"]
        summary = dict(n_colonies=len(df), area_mean=round(sizes.mean(), 1),
                       area_median=round(sizes.median(), 1), area_min=int(sizes.min()), area_max=int(sizes.max()),
                       image=f"{bgr.shape[1]}x{bgr.shape[0]}")
    else:
        summary = dict(n_colonies=0, note="无符合条件的集落，调 --min-area/--max-area 或 --invert")
    pd.DataFrame([summary]).to_csv(os.path.join(a.out_dir, "summary.csv"), index=False, encoding="utf-8-sig")
    print("[summary]", summary)
    print(f"[ok] colonies.csv / summary.csv / overlay.png -> {a.out_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--img", required=True)
    ap.add_argument("--min-area", type=int, default=30)
    ap.add_argument("--max-area", type=int, default=8000)
    ap.add_argument("--invert", action="store_true", help="亮集落暗背景时使用")
    ap.add_argument("--out-dir", default="colony_out")
    main(ap.parse_args())
