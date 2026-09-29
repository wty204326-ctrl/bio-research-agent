---
description: 单细胞分析 — 驱动 scRNA_workflow（28步 Seurat 流程，Windows R）
argument-hint: <任务描述，如：换新数据集跑全流程 / 对巨噬细胞做拟时序 / 跑细胞通讯>
---

单细胞任务：$ARGUMENTS

按 bio-research-agent 插件 scrna-runner skill 执行（**先读其 references/scrna-workflow.md**）：

1. 流程在 `C:\Users\<you>\Desktop\scRNA_workflow`，Windows R 4.6.0 跑（不是 WSL）；
2. 先 `Rscript run.R --list` 核对状态，检查 config.yaml（纯 ASCII 铁律）与需求一致；
3. 逐步骤独立 Rscript 会话执行（勿 run.R 链式）；长任务后台+轮询 workflow.log；
4. steps 15/16/18 前确认 gene_sets GMT 在位（当前缺失需先补）；
5. 大样本按手册"内存与下采样"节两阶段构建；图白底+morandi 配色；
6. n=1 数据集统计措辞红线（禁 significantly 等）。
