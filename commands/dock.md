---
description: 分子对接 — 批量 docking（WSL Vina 管线）
argument-hint: <配体×受体，如：示例糖苷×TOP2A/PTGS2/TNF>
---

执行分子对接：$ARGUMENTS

按 bio-research-agent 插件 bio-runner skill 的 references/docking-manual.md 执行（复制改造现成脚本 `run_phn_dock.py` 架构，勿从零写）。

铁律：
- 受体制备前**彻底去 HETATM**（水/共晶配体）；
- 种子 42；盒子 22 Å 起步；并行 ≤4 workers；
- **阳性对照必做**（获批药/共晶配体校准：DEX×GRα −12.22 参照）；
- 完成判断用内容级校验（数 ATOM 记录，VM 崩溃会留空白垃圾文件）；
- 产物：summary.csv（kcal/mol 矩阵+关键残基）+ poses/；图白底；无区分力靶点（如 NLRP3 NACHT 口袋）如实写局限。
