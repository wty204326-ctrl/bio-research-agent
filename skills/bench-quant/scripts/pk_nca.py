#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""药代动力学（PK）非房室分析 NCA + 曲线图 + 可选一房室拟合
用法:
  python pk_nca.py --data ct.csv --dose 10 --dose-unit mg [--route ev] [--f 1] --out-dir out
  ct.csv: time,conc[,subject][,group]（时间 h；conc 血药浓度；无 subject 列则整组一条曲线）
计算:
  Cmax/Tmax(观测) | AUC0-t(linear-up/log-down 梯形) | λz(终末段 log 回归, 自动选点: 从最后
  一点向前加直到调整R²下降; 或 --lambda-points k 固定) | t½=ln2/λz | AUC0-inf=AUC0-t+Ct/λz
  (AUC_ext%>20% 警告"终末段不足以外推") | CL(/F)=Dose/AUC0-inf | Vz(/F)=Dose/(λz·AUC0-inf)
  | AUMC/MRT(表观)
输出: nca_parameters.csv / curves.png(线性+半对数, 白底, 均值±个体) / [fit_1cmt.csv]
"""
import argparse, math, os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy import stats as st

def auc_trapezoid_logdown(t, c):
    """linear-up / log-down 梯形（上升段线性、下降段对数中点）"""
    auc = 0.0
    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        c1, c2 = c[i - 1], c[i]
        if c2 >= c1 or c1 <= 0 or c2 <= 0:
            auc += dt * (c1 + c2) / 2
        else:
            auc += dt * (c2 - c1) / (math.log(c2) - math.log(c1))
    return auc

def aumc_trapezoid(t, c):
    aumc = 0.0
    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        c1, c2 = c[i - 1], c[i]
        tm = (t[i] + t[i - 1]) / 2
        if c2 >= c1 or c1 <= 0 or c2 <= 0:
            cm = (c1 + c2) / 2
        else:
            cm = (c2 - c1) / (math.log(c2) - math.log(c1))
        aumc += dt * tm * cm
    return aumc

def lambda_z(t, c, k_fixed=None):
    """终末消除速率常数：log 线性回归；auto=从后向前加直到 adj R² 下降且斜率为负"""
    mask = (np.array(c) > 0)
    tt, cc = np.array(t)[mask], np.array(c)[mask]
    n = len(tt)
    best = None
    ks = range(3, n + 1) if k_fixed is None else [k_fixed]
    for k in ks:
        if k > n:
            break
        x, y = tt[-k:], np.log(cc[-k:])
        if len(x) < 2:
            continue
        slope, intercept, r, p, se = st.linregress(x, y)
        if slope >= 0:
            continue
        npts, r2 = k, r * r
        adj = 1 - (1 - r2) * (npts - 1) / (npts - 2) if npts > 2 else r2
        if best is None or adj > best["adj"]:
            best = dict(lam=-slope, r2=r2, adj=adj, n=npts, t_start=tt[-k])
    return best

def nca_one(t, c, dose, route, F, k_fixed):
    t = np.asarray(t, float)
    c = np.asarray(c, float)
    res = dict(Cmax=float(c.max()), Tmax=float(t[np.argmax(c)]),
               AUC_0_t=auc_trapezoid_logdown(t, c), AUMC=aumc_trapezoid(t, c))
    lz = lambda_z(t, c, k_fixed)
    if lz and lz["n"] >= 3:
        res.update(lam_z=lz["lam"], lam_z_r2=lz["r2"], lam_z_n_points=lz["n"],
                   t_half=math.log(2) / lz["lam"])
        ct = c[-1]
        res["AUC_0_inf"] = res["AUC_0_t"] + ct / lz["lam"]
        res["AUC_ext_pct"] = (ct / lz["lam"]) / res["AUC_0_inf"] * 100
        if route == "iv":
            res["CL"] = dose / res["AUC_0_inf"]
            res["Vz"] = res["CL"] / lz["lam"]
        else:
            # CL/F（表观）= Dose/AUC；给出 F≠1 时另给真 CL = F·Dose/AUC
            res["CL_F"] = dose / res["AUC_0_inf"]
            res["Vz_F"] = res["CL_F"] / lz["lam"]
            if abs(F - 1.0) > 1e-9:
                res["CL_true_if_F"] = F * dose / res["AUC_0_inf"]
                res["Vz_true_if_F"] = res["CL_true_if_F"] / lz["lam"]
        res["MRT_apparent"] = res["AUMC"] / res["AUC_0_t"]
    else:
        res["lam_z"] = np.nan
    return res

def fit_1cmt(t, c, route):
    t = np.asarray(t, float)
    c = np.asarray(c, float)
    m = c > 0
    if route == "iv":
        def f(x, c0, ke):
            return c0 * np.exp(-ke * x)
        p0 = [c.max(), 0.3]
        lo, hi = [0, 1e-4], [np.inf, 10]
    else:
        def f(x, a, ke, ka):
            return a * (np.exp(-ke * x) - np.exp(-ka * x))
        p0 = [c.max(), 0.2, 1.0]
        lo, hi = [0, 1e-4, 1.0001e-4], [np.inf, 10, 50]
    try:
        popt, _ = curve_fit(f, t[m], c[m], p0=p0, bounds=(lo, hi), maxfev=20000)
        pred = f(t[m], *popt)
        ss = 1 - np.sum((c[m] - pred) ** 2) / np.sum((c[m] - c[m].mean()) ** 2)
        if route == "iv":
            return dict(model="1cmt_iv_bolus", C0=popt[0], ke=popt[1], t_half=math.log(2) / popt[1], R2=ss)
        return dict(model="1cmt_first_order_abs", A=popt[0], ke=popt[1], ka=popt[2],
                    t_half=math.log(2) / popt[1], t_half_abs=math.log(2) / popt[2], R2=ss)
    except Exception as e:
        return dict(model="1cmt", error=str(e))

def main(a):
    os.makedirs(a.out_dir, exist_ok=True)
    df = pd.read_csv(a.data)
    cols = {c.lower().strip(): c for c in df.columns}
    tcol = cols.get(a.time_col.lower(), a.time_col)
    ccol = cols.get(a.conc_col.lower(), a.conc_col)
    df = df.rename(columns={tcol: "time", ccol: "conc"})
    for opt, key in ((a.subject, "subject"), (a.group, "group")):
        if opt and opt in cols:
            df = df.rename(columns={cols[opt]: key})
    if "subject" not in df:
        df["subject"] = "all"
    if "group" not in df:
        df["group"] = "all"
    rows, warns = [], []
    for (g, s), gd in df.groupby(["group", "subject"]):
        gd = gd.sort_values("time").dropna(subset=["conc"])
        r = dict(group=g, subject=s, n_points=len(gd),
                 t_last=float(gd["time"].max()), C_last=float(gd["conc"].iloc[-1]))
        r.update(nca_one(gd["time"].values, gd["conc"].values, a.dose, a.route, a.f, a.lambda_points))
        if "AUC_ext_pct" in r and r["AUC_ext_pct"] > 20:
            warns.append(f"{g}/{s}: AUC 外推 {r['AUC_ext_pct']:.1f}% > 20%——末段采样不足，AUC∞/CL/Vd 不可靠，建议补末点或只报 AUC0-t")
        rows.append(r)
    out = pd.DataFrame(rows)
    first = {c: out[c].first_valid_index() for c in out.columns}
    cols_order = ["group", "subject", "n_points", "Cmax", "Tmax", "AUC_0_t", "AUC_0_inf",
                  "AUC_ext_pct", "lam_z", "lam_z_r2", "lam_z_n_points", "t_half",
                  "CL", "Vz", "CL_F", "Vz_F", "CL_true_if_F", "Vz_true_if_F",
                  "MRT_apparent", "t_last", "C_last"]
    out = out[[c for c in cols_order if c in out.columns] + [c for c in out.columns if c not in cols_order]]
    out.to_csv(os.path.join(a.out_dir, "nca_parameters.csv"), index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))
    for w in warns:
        print("[warn]", w)
    if a.fit_1cmt:
        fits = []
        for (g, s), gd in df.groupby(["group", "subject"]):
            gd = gd.sort_values("time")
            f = dict(group=g, subject=s, **fit_1cmt(gd["time"].values, gd["conc"].values, a.route))
            fits.append(f)
            print(f"[1cmt {g}/{s}]", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in f.items() if k not in ("group", "subject")})
        pd.DataFrame(fits).to_csv(os.path.join(a.out_dir, "fit_1cmt.csv"), index=False, encoding="utf-8-sig")
    plot(df, a)
    print(f"[ok] nca_parameters.csv{' / fit_1cmt.csv' if a.fit_1cmt else ''} / curves.png -> {a.out_dir}")

def plot(df, a):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    groups = list(df.group.unique())
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3"][: len(groups)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for ax, scale, title in zip(axes, ["linear", "log"], ["Concentration-time (linear)", "Concentration-time (semi-log)"]):
        for g, col in zip(groups, colors):
            gdf = df[df.group == g]
            for s, sd in gdf.groupby("subject"):
                sd = sd.sort_values("time")
                ax.plot(sd.time, sd.conc, color=col, alpha=0.3, lw=1)
            m = gdf.groupby("time")["conc"].agg(["mean", "std"]).reset_index()
            ax.errorbar(m.time, m["mean"], yerr=m["std"], color=col, marker="o", ms=4,
                        capsize=3, lw=1.8, label=f"{g} mean±SD")
        if scale == "log":
            ax.set_yscale("log")
        ax.set_xlabel(f"Time ({a.time_unit})")
        ax.set_ylabel(f"Concentration ({a.conc_unit})")
        ax.set_title(title)
        ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(a.out_dir, "curves.png"), dpi=300, facecolor="white")
    plt.close(fig)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True)
    ap.add_argument("--dose", type=float, required=True, help="给药量（数值）")
    ap.add_argument("--dose-unit", default="mg")
    ap.add_argument("--route", choices=["iv", "ev"], default="ev", help="iv=静脉(e.g. bolus)；ev=血管外(口服/皮下等, 参数为 CL/F Vz/F)")
    ap.add_argument("--f", type=float, default=1.0, help="生物利用度 F（ev 且已知时填，CL/Vz 换算绝对值用）")
    ap.add_argument("--time-col", default="time")
    ap.add_argument("--conc-col", default="conc")
    ap.add_argument("--subject", default="subject")
    ap.add_argument("--group", default="group")
    ap.add_argument("--time-unit", default="h")
    ap.add_argument("--conc-unit", default="ng/mL")
    ap.add_argument("--lambda-points", type=int, default=None, help="固定终末段点数；默认自动（adj R² 最大）")
    ap.add_argument("--fit-1cmt", action="store_true", help="附加一房室拟合（IV bolus / 一级吸收）")
    ap.add_argument("--out-dir", default="pk_out")
    main(ap.parse_args())
