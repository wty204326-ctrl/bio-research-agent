#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WB(Western Blot) 条带灰度定量：检测→校验→定量→归一→统计→作图
两步用法：
  1) python wb_quant.py detect --img blot.png --lanes 6 --out-dir out
       → out/preview.png (ROI 编号图)  out/rois.csv (可手工修正坐标)
  2) python wb_quant.py quant --img blot.png --rois out/rois.csv \
       --samples samples.csv --ref-band 2 --ctrl Con --out-dir out
       → out/densities.csv  out/results.csv  out/figure.png
samples.csv 表头: lane,group,replicate （lane 编号 = rois.csv 中的 lane，从 1 起）
rois.csv   表头: lane,band,x0,y0,x1,y1 （band 序号 = 每条泳道内自上而下，从 1 起）
--ref-band: 内参蛋白所在 band 序号（如 actin 通常最低 → 序号最大）
统计: 两组 Welch t；≥3 组 one-way ANOVA + 组间 Welch t + Holm 校正
"""
import argparse, csv, math, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import find_peaks
from scipy import stats as st

def load_signal(path):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im.convert("RGBA")).convert("L")
    else:
        im = im.convert("L")
    g = np.asarray(im, dtype=float)
    return 255.0 - g, im  # 暗带 → 高信号

def smooth(x, w):
    if w < 3:
        return x
    k = np.ones(w) / w
    return np.convolve(x, k, mode="same")

def font(size=28, bold=True):
    for f in (r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
              r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default(size)

def cmd_detect(a):
    os.makedirs(a.out_dir, exist_ok=True)
    sig, im = load_signal(a.img)
    H, W = sig.shape
    colproj = smooth(sig.sum(axis=0), max(3, W // max(a.lanes * 8, 1)))
    # 泳道中心 = 列投影峰；峰数不足时用有效区域等分兜底
    dist = max(8, int(W / (a.lanes * 1.8)))
    pk, _ = find_peaks(colproj, distance=dist)
    pk = sorted(pk, key=lambda i: -colproj[i])[: a.lanes]
    pk = sorted(pk)
    if len(pk) < a.lanes:
        med = np.median(colproj)
        act = np.where(colproj > med + 0.15 * (colproj.max() - med))[0]
        lo, hi = (act[0], act[-1]) if len(act) else (0, W - 1)
        lane_w = (hi - lo) / a.lanes
        pk = [int(lo + lane_w * (i + 0.5)) for i in range(a.lanes)]
        print(f"[warn] 峰检测不足，按有效区 {lo}-{hi} 等分为 {a.lanes} 泳道", file=sys.stderr)
    # 泳道边界
    bounds = [0] + [(pk[i] + pk[i + 1]) // 2 for i in range(len(pk) - 1)] + [W]
    rois = []
    for li, cx in enumerate(pk):
        x0, x1 = bounds[li], bounds[li + 1]
        rowp = smooth(sig[:, x0:x1].sum(axis=1), 5)
        base = np.median(rowp)
        bpk, props = find_peaks(rowp, distance=max(8, H // 40),
                                prominence=max(1.0, 0.08 * (rowp.max() - base)),
                                width=3)
        for bi, (py, pl, pr) in enumerate(zip(bpk, props["left_ips"], props["right_ips"])):
            y0, y1 = max(0, int(pl)), min(H, int(pr) + 1)
            rois.append(dict(lane=li + 1, band=bi + 1, x0=x0, y0=y0, x1=x1, y1=y1))
    # 同一 band 跨泳道统一 ROI 高度（ImageJ 惯例：同排条带同尺寸框，消除强弱带截断差）
    from collections import defaultdict
    byband = defaultdict(list)
    for r in rois:
        byband[r["band"]].append(r)
    for band, rs in byband.items():
        y0, y1 = min(r["y0"] for r in rs), max(r["y1"] for r in rs)
        for r in rs:
            r["y0"], r["y1"] = y0, y1
    with open(os.path.join(a.out_dir, "rois.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["lane", "band", "x0", "y0", "x1", "y1"])
        w.writeheader()
        for r in rois:
            w.writerow(r)
    prev = im.convert("RGB")
    d = ImageDraw.Draw(prev)
    for r in rois:
        d.rectangle([r["x0"], r["y0"], r["x1"] - 1, r["y1"] - 1], outline=(255, 0, 0), width=3)
        d.text((r["x0"] + 4, max(0, r["y0"] - 34)), f'{r["lane"]}.{r["band"]}', fill=(255, 0, 0), font=font())
    prev.save(os.path.join(a.out_dir, "preview.png"))
    print(f"[ok] 泳道 {len(pk)} 个, ROI {len(rois)} 个 → preview.png + rois.csv")
    print("     请核对 preview.png：条带框错/漏 → 手工改 rois.csv 坐标后再 quant")

def local_bg(sig, r, grow=10):
    H, W = sig.shape
    x0e, y0e = max(0, r["x0"] - grow), max(0, r["y0"] - grow)
    x1e, y1e = min(W, r["x1"] + grow), min(H, r["y1"] + grow)
    ring = np.concatenate([
        sig[y0e:r["y0"], x0e:x1e].ravel(), sig[r["y1"]:y1e, x0e:x1e].ravel(),
        sig[r["y0"]:r["y1"], x0e:r["x0"]].ravel(), sig[r["y0"]:r["y1"], r["x1"]:x1e].ravel(),
    ]) if (x0e < r["x0"] or y0e < r["y0"] or x1e > r["x1"] or y1e > r["y1"]) else np.array([])
    return float(np.median(ring)) if ring.size else float(np.median(sig))

def cmd_quant(a):
    import pandas as pd
    os.makedirs(a.out_dir, exist_ok=True)
    sig, _ = load_signal(a.img)
    rois = list(csv.DictReader(open(a.rois, encoding="utf-8")))
    for r in rois:
        for k in ("lane", "band", "x0", "y0", "x1", "y1"):
            r[k] = int(r[k])
    smp = pd.read_csv(a.samples)
    smp["lane"] = smp["lane"].astype(int)
    smap = {int(r["lane"]): (str(r["group"]), str(r["replicate"])) for _, r in smp.iterrows()}
    rows = []
    for r in rois:
        roi = sig[r["y0"]:r["y1"], r["x0"]:r["x1"]]
        raw = float(roi.sum())
        bg = local_bg(sig, r)
        sub = float((roi - bg).sum())
        g, rep = smap.get(r["lane"], ("?", "?"))
        rows.append(dict(lane=r["lane"], band=r["band"], group=g, replicate=rep,
                         x0=r["x0"], y0=r["y0"], x1=r["x1"], y1=r["y1"],
                         raw=raw, bg=bg, density=sub,
                         density_clipped=max(sub, 0.0)))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(a.out_dir, "densities.csv"), index=False, encoding="utf-8-sig")
    neg = df[df.density <= 0]
    if len(neg):
        print(f"[warn] {len(neg)} 个 ROI 背景扣除后 ≤0（可能框到空位），见 densities.csv", file=sys.stderr)
    # 内参归一
    ref = df[df.band == a.ref_band]
    if not len(ref):
        sys.exit(f"[error] ref-band={a.ref_band} 不存在；可用 band 序号: {sorted(df.band.unique())}")
    reflut = {r["lane"]: r["density_clipped"] for _, r in ref.iterrows()}
    df["norm"] = df.apply(lambda r: r["density_clipped"] / reflut[r["lane"]]
                          if r["band"] != a.ref_band and reflut.get(r["lane"], 0) > 0 else np.nan, axis=1)
    tgt = df[df.band != a.ref_band].copy()
    out = []
    for band, bd in tgt.groupby("band"):
        ctrl_mean = bd[bd.group == a.ctrl]["norm"].mean()
        if not ctrl_mean or math.isnan(ctrl_mean):
            print(f"[warn] band {band}: 对照组 {a.ctrl} 均值无效，fold 用全体均值兜底", file=sys.stderr)
            ctrl_mean = bd["norm"].mean()
        bd = bd.assign(fold=bd["norm"] / ctrl_mean)
        groups = [g for g, gd in bd.groupby("group") if len(gd)]
        stats_txt = ""
        if len(groups) == 2:
            x = [bd[bd.group == groups[0]]["fold"].values, bd[bd.group == groups[1]]["fold"].values]
            p = st.ttest_ind(x[0], x[1], equal_var=False).pvalue
            stats_txt = f"Welch t-test p={p:.4g}"
        elif len(groups) > 2:
            arrs = [bd[bd.group == g]["fold"].values for g in groups]
            p = st.f_oneway(*arrs).pvalue
            pairs, ms = [], sorted(groups)
            for i in range(len(ms)):
                for j in range(i + 1, len(ms)):
                    pp = st.ttest_ind(bd[bd.group == ms[i]]["fold"].values,
                                      bd[bd.group == ms[j]]["fold"].values, equal_var=False).pvalue
                    pairs.append((ms[i], ms[j], pp))
            n = len(pairs)
            holm = sorted(pairs, key=lambda t: t[2])
            adj = {}
            run = 0.0
            for k, (ga, gb, pp) in enumerate(holm):
                run = max(run, (n - k) * pp)
                adj[(ga, gb)] = min(1.0, run)
            stats_txt = f"ANOVA p={p:.4g}; Holm 校正后: " + "; ".join(
                f"{ga} vs {gb} p={adj[(ga, gb)]:.3g}" for ga, gb, _ in pairs[:8])
        for g, gd in bd.groupby("group"):
            out.append(dict(band=band, group=g, n=len(gd), fold_mean=gd["fold"].mean(),
                            fold_sd=gd["fold"].std(ddof=1) if len(gd) > 1 else np.nan,
                            fold_sem=gd["fold"].sem() if len(gd) > 1 else np.nan))
        print(f"[band {band}] {stats_txt}")
    pd.DataFrame(out).to_csv(os.path.join(a.out_dir, "results.csv"), index=False, encoding="utf-8-sig")
    plot_bars(tgt, a, out)
    print(f"[ok] densities.csv / results.csv / figure.png → {a.out_dir}")

def stars(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"

def plot_bars(tgt, a, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    bands = sorted(tgt.band.unique())
    fig, axes = plt.subplots(1, len(bands), figsize=(4.2 * len(bands), 4.2), squeeze=False)
    for ax, band in zip(axes[0], bands):
        bd = tgt[tgt.band == band].copy()
        ctrl_mean = bd[bd.group == a.ctrl]["norm"].mean()
        bd["fold"] = bd["norm"] / ctrl_mean
        gs = [g for g in bd.group.unique()]
        means = [bd[bd.group == g]["fold"].mean() for g in gs]
        sems = [bd[bd.group == g]["fold"].sem() for g in gs]
        x = np.arange(len(gs))
        ax.bar(x, means, 0.6, yerr=sems, capsize=4, color="#4C72B0", edgecolor="black")
        for xi, g in zip(x, gs):
            ax.scatter([xi] * (bd.group == g).sum(), bd[bd.group == g]["fold"],
                       color="black", zorder=3, s=18)
        ax.axhline(1.0, ls="--", lw=0.8, color="gray")
        ax.set_xticks(x)
        ax.set_xticklabels(gs, rotation=20, ha="right")
        ax.set_ylabel(f"Fold change (band {band} / ref, vs {a.ctrl})")
        if len(gs) == 2:
            p = st.ttest_ind(bd[bd.group == gs[0]]["fold"], bd[bd.group == gs[1]]["fold"],
                             equal_var=False).pvalue
            ymax = max(np.nanmax(means) + max(np.nan_to_num(sems)), 1.2)
            ax.text(0.5, ymax * 0.97, stars(p), ha="center", fontsize=12)
    fig.suptitle("Western blot quantification")
    fig.tight_layout()
    fig.savefig(os.path.join(a.out_dir, "figure.png"), dpi=300, facecolor="white")
    plt.close(fig)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect")
    d.add_argument("--img", required=True)
    d.add_argument("--lanes", type=int, required=True)
    d.add_argument("--out-dir", default="wb_out")
    q = sub.add_parser("quant")
    q.add_argument("--img", required=True)
    q.add_argument("--rois", required=True)
    q.add_argument("--samples", required=True, help="csv: lane,group,replicate")
    q.add_argument("--ref-band", type=int, required=True, help="内参条带序号(泳道内自上而下)")
    q.add_argument("--ctrl", required=True, help="对照组名")
    q.add_argument("--out-dir", default="wb_out")
    a = ap.parse_args()
    {"detect": cmd_detect, "quant": cmd_quant}[a.cmd](a)
