#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ELISA 4PL 标准曲线拟合与浓度反算
用法: python elisa_4pl.py --std standards.csv --samples samples.csv --out-dir out
standards.csv: conc,od      （重复行=复孔；含 0 浓度孔）
samples.csv:   sample,od[,dilution]（重复行=复孔；dilution 默认 1=原液，即稀释倍数）
模型: y = d + (a-d)/(1+(x/c)^b)；浓度反算有闭式解
输出: fit_params.csv（参数+R²）/ conc.csv（样本浓度）/ curve.png（白底标准曲线）
"""
import argparse, csv, math, os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

def fourpl(x, a, b, c, d):
    return d + (a - d) / (1.0 + (np.asarray(x, dtype=float) / c) ** b)

def invert_4pl(y, a, b, c, d):
    """由 OD 反算浓度（闭式解）；出界返回 NaN"""
    y = np.asarray(y, dtype=float)
    ratio = (a - d) / (y - d)
    inner = ratio - 1.0
    ok = (y > min(a, d)) & (y < max(a, d)) & (inner > 0)
    x = np.full_like(y, np.nan)
    x[ok] = c * inner[ok] ** (1.0 / b)
    return x

def main(a):
    os.makedirs(a.out_dir, exist_ok=True)
    std = pd.read_csv(a.std)
    std.columns = ["conc", "od"]
    x, y = std["conc"].values.astype(float), std["od"].values.astype(float)
    p0 = [y.min(), 1.0, np.median(x[x > 0]) if (x > 0).any() else 1.0, y.max()]
    lo = [-np.inf, 0.05, 1e-6, -np.inf]
    hi = [np.inf, 20, np.inf, np.inf]
    popt, _ = curve_fit(fourpl, x, y, p0=p0, bounds=(lo, hi), maxfev=20000)
    ya = fourpl(x, *popt)
    r2 = 1 - np.sum((y - ya) ** 2) / np.sum((y - y.mean()) ** 2)
    A, B, C, D = popt
    pd.DataFrame([dict(a=A, b=B, c=C, d=D, R2=r2)]).to_csv(
        os.path.join(a.out_dir, "fit_params.csv"), index=False, encoding="utf-8-sig")
    print(f"[fit] a={A:.4f} b={B:.3f} c={C:.2f} d={D:.4f} R2={r2:.5f}")
    if r2 < 0.99:
        print(f"[warn] R2={r2:.4f} < 0.99，标准曲线质量差，复孔 CV 与孔位污染需排查")

    rows, warns = [], []
    if a.samples:
        smp = pd.read_csv(a.samples)
        smp = smp.iloc[:, :3]
        smp.columns = ["sample", "od", "dilution"][: smp.shape[1]] + \
                      (["dilution"] if smp.shape[1] == 2 else [])
        if smp.shape[1] == 2:
            smp["dilution"] = 1
        for sid, gd in smp.groupby("sample"):
            od = gd["od"].values.astype(float)
            dil = float(gd["dilution"].iloc[0])
            cv = od.std(ddof=1) / od.mean() * 100 if len(od) > 1 and od.mean() else np.nan
            conc = invert_4pl([od.mean()], *popt)[0]
            well = math.isfinite(conc)
            rows.append(dict(sample=sid, od_mean=od.mean(), od_cv_pct=cv, n=len(od),
                             conc_diluted=conc if well else None,
                             conc=conc * dil if well else None,
                             dilution=dil))
            if cv > 15:
                warns.append(f"{sid}: 复孔 CV={cv:.1f}% >15%")
            if not well or od.mean() <= A + 0.02 * (D - A) or od.mean() >= D - 0.02 * (D - A):
                warns.append(f"{sid}: OD 接近/超出曲线范围，结果为外推不可靠（建议稀释重测）")
        pd.DataFrame(rows).to_csv(os.path.join(a.out_dir, "conc.csv"), index=False, encoding="utf-8-sig")
        for w in warns:
            print("[warn]", w)
    plot(x, y, popt, rows, a)
    print(f"[ok] fit_params.csv / conc.csv / curve.png -> {a.out_dir}")

def plot(x, y, popt, rows, a):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4.5))
    xs = np.logspace(np.log10(max(x[x > 0].min(), 0.01)), np.log10(x.max() * 1.2), 200)
    ax.semilogx(xs, fourpl(xs, *popt), color="#4C72B0", lw=2, label="4PL fit")
    ax.scatter(x, y, color="black", zorder=3, s=25, label="standards")
    if rows:
        sm = [r["od_mean"] for r in rows]
        ax.scatter([10 ** (np.log10(popt[2]))] * len(rows), sm, marker="^", color="#DD8452",
                   zorder=3, s=40, label="samples (OD)")
    ax.set_xlabel("Standard concentration")
    ax.set_ylabel("OD")
    ax.set_title("ELISA 4PL standard curve")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out_dir, "curve.png"), dpi=300, facecolor="white")
    plt.close(fig)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--std", required=True, help="standards csv: conc,od")
    ap.add_argument("--samples", default=None, help="samples csv: sample,od[,dilution]")
    ap.add_argument("--out-dir", default="elisa_out")
    main(ap.parse_args())
