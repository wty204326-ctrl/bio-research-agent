---
name: scrna-runner
description: 单细胞 RNA-seq 分析执行器（驱动用户自有 scRNA_workflow 28 步 Seurat 流程）。10x 数据读取、QC、双细胞、归一化、Harmony 整合、SingleR+marker 注释、拟时序(monocle2/3)、细胞通讯(CellChat)、SCENIC、富集、pseudobulk 差异、核心靶点图。当用户要：单细胞/scRNA/scRNA-seq/Seurat/细胞注释/UMAP 聚类/拟时序/细胞通讯/细胞比例/亚群分析 时使用。
---

# 单细胞执行器 scrna-runner

驱动用户自有的 **scRNA_workflow**（28 步 Seurat 流程，Windows R）。**执行前必读 references/scrna-workflow.md**——含运行方式、config 铁律、步骤目录、硬依赖缺口与全部已知坑。

## 核心事实（先记住）

- 流程位置：`C:\Users\<you>\Desktop\scRNA_workflow`；**跑在 Windows R 4.6.0 + Seurat 5.5.1**（15.4GB 内存）——不是 WSL！bulk 转录组才走 WSL（bio-runner）。
- 入口：`Rscript run.R --list / --steps 2-9 / --all`；单步可独立 `Rscript scripts/NN_xx.R`。
- **推荐逐步骤独立 Rscript 会话**（run.R 链式同会话 source 全部脚本 → 包冲突 + 退出码失真，实战教训）。
- config.yaml **必须纯 ASCII**（GBK locale 下中文注释→yaml 解析 NULL→全部步骤静默 OFF，2026-09-19 血案）。
- `reference/gene_sets/` 两个 GMT **已重建（2026-09-29）**：inflammation_mm.gmt（23 条炎症/免疫通路，3285 基因）+ c2.cp.kegg_legacy.Mm.symbols.gmt（186 通路，12349 基因），msigdbr 26.1 生成，再生成脚本在同目录；⚠️ 与误删原版内容不同（原版不可恢复），steps 15/16/18 结果与旧输出不可直接比。
- 11 个恢复重建文件的验证状态（2026-09-29 小子集实测）：**01/logger/08/15/16/18/19/20 通过**；23/24 接口全通（scQC 返回 dgCMatrix 已适配，计算放后台）；**11 环境级不兼容**（monocle 2.40×新 dplyr，拟时序用 step 21）；14 未测（默认关）。修复清单见 references/scrna-workflow.md。

## 工作流

1. **明确需求**：新数据集全流程 / 换数据集 / 单个分析（拟时序/通讯/富集）/ 改图。
2. **查现状**：`Rscript run.R --list` 看步骤启用状态；读 config.yaml 核对 data_path/output_dir/study_design 与需求一致。
3. **改 config**（ASCII！切换数据集只改 project/step_02/study_design 三段）。
4. **执行**：逐步骤独立会话跑（长任务后台 + 轮询日志）；大样本先看 scrna-workflow.md 的"内存与下采样"节。
5. **产出**：output/ 下 rds+图；图一律白底（plots.R 已统一 morandi 配色）。
6. **报告**：主模型写；统计措辞红线（n=1 数据集禁 significantly 等，见手册）。

## 分工

- 本 skill：scRNA（这套 Windows 流程）。
- bio-runner：bulk 转录组/蛋白组（WSL rna env）、网药对接。
- r-plot skill：出版级统计图（156 模板 + morandi 配色，与本项目同源）。
