---
description: 样本量/检验效能计算 — 均数/率/配对/ANOVA/相关
argument-hint: <设计参数，如：两组均数 10 vs 12 SD=2 算样本量 / 30例效能多少>
---

样本量计算：$ARGUMENTS

用 bench-quant skill 的 `scripts/samplesize_calc.py`（statsmodels）：
```
--test means  --mean1 --mean2 --sd        两组均数
--test paired --mean1 --mean2 --sd        配对（sd=差值SD）
--test props  --p1 --p2                   两组率
--test anova  --k --f                     单因素ANOVA
--test corr   --r                         相关
[--alpha 0.05 --power 0.8 --ratio 1] [--n 30]（给 n 改算效能）
```
- 输出 0.8/0.9 效能所需每组 n + 10-15% 脱落率建议；
- 基准已验证：d=1→17/组、率 0.3vs0.5→93/组（Cohen h）；
- 回答时附效应量解释与设计假设声明（双侧 α、方差齐性）。
