---
description: 图像裁切/拼接/组图/比例尺/标注 — 论文汇报图一键处理
argument-hint: <需求描述，如：把这两张图拼成 A B 面板 / 裁出条带区域 / 加50μm比例尺>
---

图像处理：$ARGUMENTS

用 bio-research-agent 插件 figure-forge skill 的 scripts/figops.py（输出一律纯白底）：

子命令：`info` 尺寸 | `autocrop` 去白边 | `crop --box x0,y0,x1,y1` 裁切 | `stitch --imgs ... --cols N --labels A,B,C` 拼接 | `scalebar --px N --um M` 比例尺 | `whitebg` 铺白 | `annotate --box/--arrow/--text` 标注。

规则：先 info 定坐标；每步产物用 Read 自查迭代；拼接前逐张 autocrop；比例尺换算需真实视野信息勿臆测；完成后报告尺寸/布局/字母对应。
