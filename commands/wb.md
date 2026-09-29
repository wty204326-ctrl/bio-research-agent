---
description: Western Blot 条带灰度定量 — 检测/校验/内参归一/统计/作图/GraphPad
argument-hint: <膜图路径 + 分组说明，如：blot.png 6泳道 Con Con Model Model Treat Treat，actin为内参>
---

WB 定量：$ARGUMENTS

按 bio-research-agent 插件 bench-quant skill 执行（scripts 在该 skill 目录）：

1. `wb_quant.py detect` 自动检测 → **Read 查看 preview.png**，框错/漏改 rois.csv；
2. 写 samples.csv（lane,group,replicate）→ `wb_quant.py quant --ref-band <内参序号> --ctrl <对照组>`；
3. 饱和条带（大片纯黑）→ 提示用户换非饱和曝光，不可定量；
4. 输出 densities/results/figure.png（白底）；需 GraphPad 时用 `make_pzfx.py` 生成 .pzfx（长表 category,group,value），提醒用户双击打开验证一次兼容性。
