# scRNA_workflow 操作手册（28 步 Seurat 流程，通用版）

适用于 config 驱动的 Seurat 流水线（本手册按 01-28 步结构编写，坑位来自真实恢复/重建流程的实机验证）。

## 位置与运行

- 工作流路径：`<SCRNA_WORKFLOW_DIR>`（用户自定义；Windows R ≥4.6 + Seurat 5.x，内存受限机器注意后文下采样节）
- 运行：
  ```
  Rscript run.R --list        # 步骤与启用状态（先跑这个）
  Rscript run.R --steps 2-9   # 主链路（自动补依赖）
  Rscript scripts/09_annotate.R   # 单步独立运行
  ```
  日志：项目根 workflow.log。
- **推荐逐步骤独立 Rscript 会话**——run.R 同一会话顺序 source 全部步骤，长链有包冲突 + 退出码失真风险；小规模链式可行，大数据量请拆步。

## config.yaml 铁律

- **纯 ASCII**：UTF-8 中文注释在 Windows GBK locale 下让 `yaml::read_yaml` 返回 NULL → 所有步骤显示 OFF、静默不跑（真实血案）。
- 换数据集只动三段：`project.output_dir`、`step_02_read_data`（data_path/min_cells/min_features）、`study_design`。

## 步骤目录（01-28）

| 步骤 | 内容 | 关键坑 |
|---|---|---|
| 01 | 包加载 | 恢复/重写脚本先冒烟 |
| 02 | 读 10x → Seurat 对象 | 大样本见下节"内存与下采样" |
| 03 | QC（nFeature/UMI/MT/HB） | 参数在 config |
| 04 | DoubletFinder | 大样本内存风险，可 standalone |
| 05 | 细胞周期打分 | |
| 06 | 归一化（SCT 3000 HVG） | 回归 S/G2M |
| 07 | Harmony+聚类 | **调色板需 ≥ 簇数（动态扩色）** |
| 08 | SingleR 注释 | 曾崩在存盘前 → 08b 多数票重建（簇级近似需披露） |
| 09 | marker 注释（两轮） | 文件头 BOM 会致 unexpected token，剥除 |
| 10 | 多方法整合对比 | |
| 11 | Monocle2 拟时序 | ⚠️ monocle 2.40 与新版 dplyr 不兼容（内部调已删接口）；拟时序建议用 21；如必须跑：`VGAM::negbinomial.size()`、estimateSizeFactors/estimateDispersions 摘掉 monocle:: 前缀 |
| 12 | CellChat | net$weight 聚合矩阵；netVisual_bubble 参数 font.size/angle.x，pairLR.use 不兼容→手动 ggplot |
| 13 | pySCENIC | Python venv 自建；无 GPU；ctx 用 --mode dask_multiprocessing --num_workers 1 |
| 14 | CopyKAT | 默认关 |
| 15/16 | ssGSEA / AUCell | 依赖 gene_sets GMT（缺失先重建；重建版与原版不可直比） |
| 17 | GO/KEGG | pathway_filter 关键词表按自己口径过一遍 |
| 18 | GSEA | 排序表用 AverageExpression 组间均值差（不能用 only.pos markers）；矩阵写 CSV 先 as.data.frame |
| 19 | 多火山 | EnhancedVolcano 未装可用 ggplot2 |
| 20 | ClusterGVis | 依赖 09 目录的 **markers_all.csv（不只 rds）**；API 按安装版本核对 |
| 21 | Monocle3 | learn_graph 必须 use_partition=FALSE |
| 22 | scMetabolism | 基因名 toupper（人源 KEGG 集匹配） |
| 23/24 | scTenifoldKnk/Net | 需 library(Seurat)；scQC 新版不认 minDimension/maxDimension，且**直接返回 dgCMatrix（非 list）**；小子集会触发包内过滤边界 |
| 25 | pseudobulk DE（每细胞类型） | |
| 26 | 逆转分析（失调∩回复∩靶点集） | |
| 27 | 核心靶点图 | Seurat 新版 FetchData 用 layer= 不是 slot= |
| 28 | UMAP 重标注 | 数字版留 *_numbered 备份 |

## 内存与下采样（大样本实战）

- 大细胞数（>5 万）直接 Seurat merge 易 OOM → **矩阵层合并**：逐样本 counts 稀疏矩阵 cbind + meta + 一次 CreateSeuratObject；两阶段：stage1 逐样本过滤/下采样存 rds，stage2 全新会话合并。
- 确定性下采样（固定 seed、每样本固定 N）必须写进方法学。
- 复用旧输出跑下游：把上游目录的 **rds 与 CSV（markers_all.csv 等）一并**拷到新输出树。
- GMT 重建：msigdbr 生成（鼠源命名与人类库不同：LPS 要写 MEDIATED_SIGNALING、部分 KEGG 集鼠源不存在），生成脚本随用随写，重建版 ≠ 原版要披露。

## 通用坑

- Seurat `AverageExpression`/`AggregateExpression` 把组名 `_` 转 `-`；slot+layer 双传参报 formal argument matched twice。
- babelgene 鼠→人 ortholog：输入鼠源时 `human=FALSE`。
- 调色板数量 ≥ 簇数；图 `bg="white"`；配色建议统一莫兰迪（r-plot skill 的 morandi_palette.R 思路）。
- 报告措辞红线：n=1 数据禁 significantly/causal 等；下采样、簇级近似注释写进方法学与局限。
