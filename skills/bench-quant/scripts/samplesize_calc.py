#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""样本量/检验效能计算器（statsmodels）
用法示例:
  python samplesize_calc.py --test means  --mean1 10 --mean2 12 --sd 2            # 两组均数
  python samplesize_calc.py --test paired --mean1 10 --mean2 11 --sd 2            # 配对（sd=差值标准差）
  python samplesize_calc.py --test props  --p1 0.3 --p2 0.5                       # 两组率
  python samplesize_calc.py --test anova  --k 4 --f 0.25                          # 单因素ANOVA(Cohen f)
  python samplesize_calc.py --test corr   --r 0.3                                 # 相关
可选: --alpha 0.05 --power 0.8 --ratio 1（对照组:实验组样本比）; --n 30 时改算该 n 的效能
输出: 各 power(0.8/0.9) 所需每组 n + 效应量；给定 --n 时输出 achieved power
"""
import argparse, math
import numpy as np
from statsmodels.stats.power import (TTestIndPower, TTestPower, NormalIndPower, FTestAnovaPower)

def main(a):
    alpha, power = a.alpha, a.power
    out = {"test": a.test, "alpha": alpha, "power": power, "ratio": a.ratio}
    if a.test == "means":
        d = abs(a.mean2 - a.mean1) / a.sd
        out.update(design="two independent means (Cohen d)", effect_size=d)
        solve = lambda pw: math.ceil(TTestIndPower().solve_power(effect_size=d, alpha=alpha, power=pw, ratio=a.ratio))
    elif a.test == "paired":
        d = abs(a.mean2 - a.mean1) / a.sd
        out.update(design="paired means (d of differences)", effect_size=d)
        solve = lambda pw: math.ceil(TTestPower().solve_power(effect_size=d, alpha=alpha, power=pw))
    elif a.test == "props":
        h = 2 * math.asin(math.sqrt(a.p2)) - 2 * math.asin(math.sqrt(a.p1))
        out.update(design="two proportions (Cohen h)", effect_size=h)
        solve = lambda pw: math.ceil(NormalIndPower().solve_power(effect_size=h, alpha=alpha, power=pw, ratio=a.ratio))
    elif a.test == "anova":
        out.update(design=f"one-way ANOVA, k={a.k} (Cohen f)", effect_size=a.f)
        solve = lambda pw: math.ceil(FTestAnovaPower().solve_power(effect_size=a.f, k_groups=a.k, alpha=alpha, power=pw))
    elif a.test == "corr":
        z = 0.5 * math.log((1 + a.r) / (1 - a.r))
        out.update(design="Pearson correlation (Fisher z)", effect_r=a.r)
        def solve(pw):
            n = ((1.959964 + {0.8: 0.841621, 0.9: 1.281552}.get(pw, 0.84)) / z) ** 2 + 3
            return math.ceil(n)
    else:
        raise SystemExit(f"未知检验类型 {a.test}")
    if a.n:
        if a.test == "means":
            pw = TTestIndPower().power(effect_size=out["effect_size"], nobs1=a.n, alpha=alpha, ratio=a.ratio)
        elif a.test == "paired":
            pw = TTestPower().power(effect_size=out["effect_size"], nobs=a.n, alpha=alpha)
        elif a.test == "props":
            pw = NormalIndPower().power(effect_size=out["effect_size"], nobs1=a.n, alpha=alpha, ratio=a.ratio)
        elif a.test == "anova":
            pw = FTestAnovaPower().power(effect_size=out["effect_size"], nobs=a.n, k_groups=a.k, alpha=alpha)
        else:
            z = 0.5 * math.log((1 + a.r) / (1 - a.r))
            pw = 1 - math.sqrt(2 / math.pi) * math.exp(-((math.sqrt(a.n - 3) * z - 1.959964) ** 2 / 2))
        out.update(given_n_per_group=a.n, achieved_power=float(pw))
        print(f"[result] {out['design']}: effect={out['effect_size']:.3f}, n/group={a.n} -> power={pw:.3f}")
    else:
        n80, n90 = solve(0.8), solve(0.9)
        out.update(n_per_group_power80=n80, n_per_group_power90=n90,
                   note=f"再加 10-15% 脱落率 → 实际入组 ≈ {math.ceil(n80 * 1.1)}-{math.ceil(n80 * 1.15)}/组")
        print(f"[result] {out['design']}: effect={out['effect_size']:.3f}")
        print(f"  power 0.8 → 每组 n = {n80}")
        print(f"  power 0.9 → 每组 n = {n90}")
        print(f"  {out['note']}")
    import json
    print(json.dumps({k: v for k, v in out.items() if k != 'design'}, ensure_ascii=False))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--test", required=True, choices=["means", "paired", "props", "anova", "corr"])
    ap.add_argument("--mean1", type=float); ap.add_argument("--mean2", type=float)
    ap.add_argument("--sd", type=float); ap.add_argument("--p1", type=float); ap.add_argument("--p2", type=float)
    ap.add_argument("--k", type=int, default=3); ap.add_argument("--f", type=float)
    ap.add_argument("--r", type=float)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--power", type=float, default=0.8)
    ap.add_argument("--ratio", type=float, default=1.0)
    ap.add_argument("--n", type=int, default=None, help="给定每组 n 时改算 achieved power")
    main(ap.parse_args())
