---
description: qPCR ΔΔCt 分析 — Ct 表解析/统计/作图/GraphPad
argument-hint: <Ct 表路径 + 内参与对照，如：ct.csv 内参GAPDH 对照Con>
---

qPCR 分析：$ARGUMENTS

按 bio-research-agent 插件 bench-quant skill 执行：

1. `qpcr_ddct.py --data <表> --ref <内参基因> --ctrl <对照组> --out-dir out`（长表/宽表/CSV/XLSX 自动识别）；
2. 查看 warnings.txt（技术重复 SD>0.3、Ct≥35）并向用户如实转述；
3. 输出 per_sample.csv / summary.csv / figure.png（统计在 ΔCt 层，误差棒=95%CI 变换）；
4. 需 GraphPad 时：summary 或 per_sample 转长表 → `make_pzfx.py` 生成 .pzfx 供 Prism 二次编辑。
