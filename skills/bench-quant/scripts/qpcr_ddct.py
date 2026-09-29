#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qPCR ΔΔCt 分析：Ct 表 → ΔCt → 组间统计(ΔCt 层) → fold change → 图
用法: python qpcr_ddct.py --data ct.csv --ref GAPDH --ctrl Con --out-dir out

输入（CSV/XLSX 皆可，自动识别）：
  长表: 列含 Sample, Group(或 Treatment), Gene(或 Target), Ct
  宽表: 首列 Sample, 第二列(可选) Group, 其余列 = 基因名, 单元格 = Ct（技术重复=同名样本多行）
统计原则: 检验在 ΔCt 层做（文献规范），不做 fold change 上的 t 检验；
          图上柱 = mean FC，误差棒 = ΔCt 层 95%CI 变换到 FC 域。
输出: per_sample.csv / summary.csv / figure.png / warnings.txt
"""
import argparse, math, os, sys
import numpy as np
import pandas as pd
from scipy import stats as st

COLS = dict(sample=("sample", "样品", "sampleid"), group=("group", "treatment", "组", "分组"),
            gene=("gene", "target", "基因"), ct=("ct", "cq", "c_t"))

def norm_col(c, kind):
    return next((x for x in COLS[kind] if x == str(c).strip().lower()), None)

def read_data(path):
    df = pd.read_excel(path) if path.lower().endswith((".xlsx", ".xls")) else pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    m = {k: next((c for c in df.columns if norm_col(c, k)), None) for k in COLS}
    if all(m.values()):
        long = df.rename(columns={m["sample"]: "Sample", m["group"]: "Group",
                                  m["gene"]: "Gene", m["ct"]: "Ct"})[["Sample", "Group", "Gene", "Ct"]]
        return long, "long"
    # 宽表: 首列 Sample, 次列可选 Group
    cols = list(df.columns)
    sample_c, group_c = cols[0], (cols[1] if len(cols) > 2 and m["group"] else None)
    genes = [c for c in cols if c not in (sample_c, group_c)]
    rows = []
    for _, r in df.iterrows():
        for g in genes:
            rows.append(dict(Sample=r[sample_c], Group=r[group_c] if group_c else "All", Gene=g, Ct=r[g]))
    return pd.DataFrame(rows), "wide"

def main(a):
    os.makedirs(a.out_dir, exist_ok=True)
    warns = []
    long, mode = read_data(a.data)
    print(f"[i] 识别为{mode}表: {long.Sample.nunique()} 样本, {long.Gene.nunique()} 基因: {sorted(long.Gene.unique())}")
    long["Ct"] = pd.to_numeric(long["Ct"], errors="coerce")
    bad = long[long["Ct"].isna()]
    if len(bad):
        warns.append(f"{len(bad)} 行 Ct 非数值已剔除")
        long = long.dropna(subset=["Ct"])
    long = long[long["Ct"] > 0]
    undet = long[long["Ct"] >= 35]
    if len(undet):
        warns.append(f"{len(undet)} 行 Ct≥35（接近检测极限，结果不可靠，仍参与计算，请人工复核）")
    # 技术重复合并（同名 Sample+Gene 取均值）
    rep = long.groupby(["Sample", "Gene"]).size()
    multi = rep[rep > 1]
    for (s, g), n in multi.items():
        cts = long[(long.Sample == s) & (long.Gene == g)]["Ct"]
        if len(cts) > 1 and cts.std(ddof=0) > 0.3:
            warns.append(f"技术重复离散偏大 Sample={s} Gene={g} SD={cts.std(ddof=0):.2f} (>0.3)")
    agg = long.groupby(["Sample", "Group", "Gene"], as_index=False)["Ct"].mean()
    # ΔCt
    ref = agg[agg.Gene == a.ref]
    if not len(ref):
        sys.exit(f"[error] 内参基因 {a.ref} 不在数据中；可用基因: {sorted(agg.Gene.unique())}")
    reflut = {r["Sample"]: r["Ct"] for _, r in ref.iterrows()}
    missing_ref = set(agg.Sample) - set(reflut)
    if missing_ref:
        sys.exit(f"[error] 这些样本缺内参 Ct: {sorted(missing_ref)}")
    agg["dCt"] = agg.apply(lambda r: r["Ct"] - reflut[r["Sample"]], axis=1)
    tg = agg[agg.Gene != a.ref].copy()
    ctrl_samples = tg[tg.Group == a.ctrl]
    if not len(ctrl_samples):
        sys.exit(f"[error] 对照组 {a.ctrl} 不存在；可用组: {sorted(tg.Group.unique())}")
    per, summ = [], []
    for g, gd in tg.groupby("Gene"):
        cm = gd[gd.Group == a.ctrl]["dCt"].mean()
        gd = gd.assign(ddCt=gd["dCt"] - cm, FC=2 ** -(gd["dCt"] - cm), log2FC=-(gd["dCt"] - cm))
        gs = [x for x, _ in gd.groupby("Group")]
        if len(gs) == 2:
            x1 = gd[gd.Group == gs[0]]["dCt"].values
            x2 = gd[gd.Group == gs[1]]["dCt"].values
            test = f"Welch t-test p={st.ttest_ind(x1, x2, equal_var=False).pvalue:.4g}"
        else:
            test = f"ANOVA p={st.f_oneway(*[gd[gd.Group == x]['dCt'].values for x in gs]).pvalue:.4g}"
        print(f"[{g} vs {a.ref}] {test}")
        for grp, ggd in gd.groupby("Group"):
            m = ggd["log2FC"].mean()
            se = ggd["log2FC"].sem()
            n = len(ggd)
            lo, hi = (2 ** (m - 1.96 * se), 2 ** (m + 1.96 * se)) if n > 1 and not math.isnan(se) else (np.nan, np.nan)
            summ.append(dict(Gene=g, Group=grp, n=n, FC_mean=2 ** m, FC_low95=lo, FC_high95=hi,
                             log2FC=m, log2FC_sd=ggd["log2FC"].std(ddof=1) if n > 1 else np.nan))
        per.append(gd)
    per = pd.concat(per)
    per.to_csv(os.path.join(a.out_dir, "per_sample.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(summ).to_csv(os.path.join(a.out_dir, "summary.csv"), index=False, encoding="utf-8-sig")
    if warns:
        open(os.path.join(a.out_dir, "warnings.txt"), "w", encoding="utf-8").write("\n".join(warns))
        for w in warns:
            print("[warn]", w)
    plot(per, pd.DataFrame(summ), a)
    print(f"[ok] per_sample.csv / summary.csv / figure.png → {a.out_dir}")

def plot(per, summ, a):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    genes = sorted(per.Gene.unique())
    fig, axes = plt.subplots(1, len(genes), figsize=(4.2 * len(genes), 4.2), squeeze=False)
    for ax, g in zip(axes[0], genes):
        sg = summ[summ.Gene == g].reset_index(drop=True)
        x = np.arange(len(sg))
        ax.bar(x, sg["FC_mean"], 0.6, color="#DD8452", edgecolor="black")
        err_lo = np.clip(sg["FC_mean"] - sg["FC_low95"], 0, None)
        err_hi = np.clip(sg["FC_high95"] - sg["FC_mean"], 0, None)
        ax.errorbar(x, sg["FC_mean"], yerr=[err_lo, err_hi], capsize=4, fmt="none", ecolor="black")
        for xi, (_, r) in zip(x, sg.iterrows()):
            pts = per[(per.Gene == g) & (per.Group == r["Group"])]["FC"]
            ax.scatter([xi] * len(pts), pts, color="black", zorder=3, s=18)
        ax.axhline(1.0, ls="--", lw=0.8, color="gray")
        ax.set_xticks(x)
        ax.set_xticklabels(sg["Group"], rotation=20, ha="right")
        ax.set_ylabel(f"Fold change ({g} vs {a.ctrl})")
    fig.suptitle(f"qPCR 2^(-ΔΔCt), ref = {a.ref}")
    fig.tight_layout()
    fig.savefig(os.path.join(a.out_dir, "figure.png"), dpi=300, facecolor="white")
    plt.close(fig)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, help="Ct 表 csv/xlsx")
    ap.add_argument("--ref", required=True, help="内参基因名，如 GAPDH")
    ap.add_argument("--ctrl", required=True, help="对照组名")
    ap.add_argument("--out-dir", default="qpcr_out")
    main(ap.parse_args())
