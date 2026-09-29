---
description: ELISA 标准曲线与浓度计算 — 4PL 拟合/反算/CV 质控
argument-hint: <标准曲线+样本 OD 表路径，如：std.csv 和 smp.csv，样本稀释100倍>
---

ELISA 分析：$ARGUMENTS

用 bench-quant skill 的 `scripts/elisa_4pl.py`：
```
python scripts/elisa_4pl.py --std std.csv --samples smp.csv --out-dir out
```
- std.csv: `conc,od`（重复行=复孔，含 0 孔）；samples: `sample,od[,dilution]`；
- 输出 fit_params（a/b/c/d/R²，R²<0.99 会告警）、conc.csv（浓度+复孔 CV）、curve.png；
- OD 出曲线范围的样本标为外推不可靠 → 建议用户稀释重测；
- 表格呈现 + 稀释倍数换算复核。
