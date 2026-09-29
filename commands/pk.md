---
description: 药代动力学计算 — NCA(Cmax/AUC/t½/CL/Vd) + 半对数曲线 + 可选一房室拟合
argument-hint: <药时数据+剂量，如：pk.csv 口服 10mg/kg 一组三只>
---

PK 分析：$ARGUMENTS

用 bench-quant skill 的 `scripts/pk_nca.py`：
```
python scripts/pk_nca.py --data ct.csv --dose 10 --dose-unit mg/kg --route ev --fit-1cmt --out-dir out
```
- ct.csv：`time,conc,subject,group`（多动物/多组自动各算一套）；
- 先核对采样设计：末段 ≥3 个下降点才有 λz；AUC 外推 >20% 会警告（此时只报 AUC0-t）；
- 输出 nca_parameters.csv + curves.png（线性/半对数，白底）+ fit_1cmt.csv（可选）；
- 解读时区分 CL/F（表观）与真值列（仅 --f≠1 时给出）；报告附剂量/途径/单位与个体 vs 均值说明。
