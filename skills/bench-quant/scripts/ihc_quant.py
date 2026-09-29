#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IHC(DAB)/IF 图像定量：阳性面积比、平均光密度、IOD、阳性细胞计数
用法:
  python ihc_quant.py --img ihc.png --mode dab [--roi x,y,w,h] [--count-cells] [--out-dir out]
  python ihc_quant.py --img if.png --mode if --marker 2 [--count-cells --nuclei-channel 2] ...
模式 dab: Ruifrok 颜色去卷积（苏木素+DAB），Otsu 定阳性
模式 if:  --marker 通道号(0=R,1=G,2=B 或 gray)为Marker强度，Otsu 定阳性
count-cells: 用苏木素(或 --nuclei-channel)通道做核分割(watershed)，输出每核Marker均值与阳性核比例
输出: stats.csv / overlay.png / cells.csv(计数时)
"""
import argparse, os
import numpy as np
import cv2
import pandas as pd

# Ruifrok 标准染色向量 (RGB)，第三列为正交补
HEMATOXYLIN = np.array([0.644, 0.717, 0.267])
DAB = np.array([0.268, 0.570, 0.776])

def stain_matrix():
    third = np.cross(HEMATOXYLIN, DAB)
    third /= np.linalg.norm(third)
    return np.stack([HEMATOXYLIN, DAB, third], axis=1)  # 列=染色

def to_od(rgb):
    return -np.log10(np.clip(rgb.astype(float) + 1, 1, 256) / 256.0)

def deconv(rgb):
    M = stain_matrix()
    od = to_od(rgb)
    # od = M @ conc（列向量约定）→ 行向量形式 conc = od @ inv(M)^T
    conc = od.reshape(-1, 3) @ np.linalg.inv(M).T
    return conc.reshape(rgb.shape[:2] + (3,))

def to_u8(arr):
    """归一化到 0-255 再转 uint8（光密度值小，直接 cast 会全 0）"""
    arr = np.clip(arr, 0, None)
    if arr.max() <= 0:
        return np.zeros(arr.shape, dtype=np.uint8)
    return (arr / arr.max() * 255).astype(np.uint8)

def otsu_bool(arr):
    t, _ = cv2.threshold(arr.astype(np.uint8), 0, 255, cv2.THRESH_OTSU)
    return arr > t, t

def segment_nuclei(chan_u8):
    blur = cv2.GaussianBlur(chan_u8, (3, 3), 0)
    m, _ = otsu_bool(blur)
    m = m.astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel, iterations=1)
    dist = cv2.distanceTransform(m, cv2.DIST_L2, 3)
    _, markers = cv2.connectedComponents((dist > 1).astype(np.uint8))
    markers = markers + 1
    markers[m == 0] = 0
    ws = cv2.watershed(np.dstack([blur] * 3), markers.astype(np.int32))
    return ws

def main(a):
    os.makedirs(a.out_dir, exist_ok=True)
    bgr = cv2.imread(a.img, cv2.IMREAD_COLOR)
    if bgr is None:
        raise SystemExit(f"读不到图: {a.img}")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    if a.roi:
        x, y, w, h = [int(v) for v in a.roi.split(",")]
        rgb = rgb[y:y + h, x:x + w]
    H, W = rgb.shape[:2]
    total_px = H * W

    if a.mode == "dab":
        conc = deconv(rgb)
        dab_u8 = to_u8(np.clip(conc[:, :, 1], 0, None))
        hem_u8 = to_u8(np.clip(conc[:, :, 0], 0, None))
        pos, t_dab = otsu_bool(cv2.GaussianBlur(dab_u8, (3, 3), 0))
        marker_map = np.clip(conc[:, :, 1], 0, None)
        marker_u8 = dab_u8
    else:
        if a.marker == "gray":
            marker_map = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        else:
            marker_map = rgb[:, :, int(a.marker)]
        pos, t_dab = otsu_bool(cv2.GaussianBlur(to_u8(marker_map), (3, 3), 0))
        marker_u8 = to_u8(marker_map)
        hem_u8 = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # 手动阈值覆盖（u8 0-255 标尺）：弱染色被 Otsu 漏判时用，如 --pos-thresh 60
    if a.pos_thresh is not None:
        t_dab = float(a.pos_thresh)
        pos = marker_u8 > t_dab

    stats = {
        "mode": a.mode, "roi": a.roi or "full", "area_px": total_px,
        "positive_area_pct": pos.sum() / total_px * 100,
        "mean_marker_intensity": float(marker_map[pos].mean()) if pos.any() else None,
        "IOD": float(marker_map[pos].sum()) if pos.any() else 0,
        "otsu_threshold": float(t_dab),
    }
    cells = None
    if a.count_cells:
        if a.mode == "if":
            nuc = to_u8(rgb[:, :, int(a.nuclei_channel)])
        else:
            nuc = hem_u8
        ws = segment_nuclei(nuc)
        ids = [i for i in np.unique(ws) if i > 1]
        rows = []
        for i in ids:
            m = ws == i
            if m.sum() < 10:
                continue
            rows.append(dict(cell_id=len(rows) + 1, area_px=int(m.sum()),
                             marker_mean=float(marker_map[m].mean()),
                             marker_mean_u8=float(marker_u8[m].mean())))
        cells = pd.DataFrame(rows)
        if len(cells):
            cells["positive"] = cells["marker_mean_u8"] > t_dab
            stats.update(n_cells=len(cells),
                         positive_cells=int(cells["positive"].sum()),
                         positive_cell_pct=float(cells["positive"].mean() * 100))
    pd.DataFrame([stats]).to_csv(os.path.join(a.out_dir, "stats.csv"), index=False, encoding="utf-8-sig")
    if cells is not None:
        cells.to_csv(os.path.join(a.out_dir, "cells.csv"), index=False, encoding="utf-8-sig")
    overlay = rgb.astype(float)
    overlay[pos, 0] = 0.6 * overlay[pos, 0] + 0.4 * 255
    overlay[pos, 1] = 0.6 * overlay[pos, 1]
    overlay[pos, 2] = 0.6 * overlay[pos, 2]
    cv2.imwrite(os.path.join(a.out_dir, "overlay.png"),
                cv2.cvtColor(overlay.astype(np.uint8), cv2.COLOR_RGB2BGR))
    print("[stats]", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in stats.items()})
    print(f"[ok] stats.csv / overlay.png{' / cells.csv' if cells is not None else ''} -> {a.out_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--img", required=True)
    ap.add_argument("--mode", choices=["dab", "if"], default="dab")
    ap.add_argument("--roi", default=None, help="x,y,w,h 像素")
    ap.add_argument("--marker", default="2", help="if 模式 Marker 通道：0=R,1=G,2=B 或 gray")
    ap.add_argument("--nuclei-channel", default="2", help="if 模式核通道（DAPI 通常=B=2）")
    ap.add_argument("--count-cells", action="store_true")
    ap.add_argument("--pos-thresh", type=int, default=None,
                    help="手动阳性阈值(0-255)，覆盖 Otsu（弱染色偏保守时用）")
    ap.add_argument("--out-dir", default="ihc_out")
    main(ap.parse_args())
