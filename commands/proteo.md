---
description: 蛋白组学分析 — 强度矩阵→归一/补值/limma差异→火山/热图/富集
argument-hint: <强度矩阵路径+分组，如：intensity.csv + samples.csv（LFQ/TMT/DIA通用）>
---

蛋白组学分析：$ARGUMENTS

按 bio-research-agent 插件 bio-runner skill 的 references/proteomics-manual.md 执行（WSL rna env）：

1. 平台识别（MaxQuant 先过滤 Reverse/Contaminant/site-only，取 LFQ，蛋白名用 Gene names）；
2. log2 → 每组≥50%有值过滤 → 列中位数归一 → 缺失值策略（MNAR 左移补值，敏感性双跑）；
3. limma 差异（topTable ID 在 rownames；makeContrasts 命名传参）；adj.P<0.05 + |log2FC| 按数据分布定阈；
4. 火山图/热图(pheatmap)/富集(clusterProfiler，timeout=900)——图全部 bg="white"；
5. 执行前读 references/wsl-ops.md 与 r-analysis-pitfalls.md；长任务 setsid nohup。
