---
description: ADMET 成药性预测 — 调本机控制台(8100) 24端点
argument-hint: <SMILES 或化合物名，如：槲皮素的SMILES预测全套ADMET>
---

ADMET 预测：$ARGUMENTS

1. 化合物名先转 SMILES：`mcp__biomed__pubchem_compound`（取 CanonicalSMILES/ConnectivitySMILES）；
2. `mcp__biomed__admet_predict`（smiles_list）→ 24 端点；控制台没开会报错并提示先双击桌面「ADMET控制台_实验室部署包\ADMET预测模型\启动.bat」（首次加载模型数十秒，重试即可）；
3. 输出中文小结表（按 吸收/分布/代谢/排泄/毒性 分组），标注模型版本与"预测值非实验值"；
4. 多分子比较时列对照表，标出红旗端点（hERG/DILI/AMES 阳性）。
