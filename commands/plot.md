---
description: R 绘图 — 调用 r-plot 模板库出 SCI 图（156 种 + 莫兰迪配色）
argument-hint: <数据文件+图型需求，如：data.csv 画分组箱线图带显著性 / 火山图>
---

R 绘图：$ARGUMENTS

1. **优先用 Skill 工具加载 r-plot skill**（本机已装：156 种模板=106 通用+50 SCI，catalog.md 路由选图，`scripts/run_r.sh` 统一入口修中文坑）；
2. r-plot 不可用时按其路由表思路手写 ggplot2：模板目录 `C:/Users\<you>/.agents/skills/r-plot/templates/{106,50sci}/` 可直接参考代码；
3. 配色默认莫兰迪（`r-plot/scripts/morandi_palette.R`：morandi_qual 离散 26 色 / morandi_div 热图 / 两组对比 #56A1B8 vs #DEAEC3）；
4. 红线：所有图 `bg="white"` 纯白背景；模板只读，复制到工作目录改；
5. 位图裁拼（组图/字母/比例尺）用 figure-forge 的 figops.py，与统计图分工。
