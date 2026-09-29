# 蛋白组学分析手册（通用强度矩阵 → limma 差异 → 图/富集）

执行环境：WSL conda `rna` env（limma/pheatmap/clusterProfiler 已装，13 包验证过）。转录组流程（DESeq2/edgeR）同 env，见 r-analysis-pitfalls.md。

## 输入约定

**通用强度矩阵**（所有平台通吃）：
- `protein × sample` 强度矩阵 CSV（行=蛋白，用基因符号或 UniProt 列；列=样本）
- 分组表 `sample,group` 两列 CSV（或列名带组前缀自动解析）
- 平台特定预处理：
  - **MaxQuant**：`proteinGroups.txt` → 先过滤 `Reverse==+`、`Only identified by site==+`、`Potential contaminant==+` → 取 LFQ intensity 列；蛋白名用 `Gene names` 首符号
  - **TMT**：取 correction 后 reporter 强度；注意批次/channel 设计；组内中位数归一前先 log2
  - **DIA**（DIA-NN/Spectronaut report.tsv）：取 PG.Quantity 或 LFQ，去 Contaminant

## 标准流程（R 骨架，按数据微调）

```r
library(limma)
mat <- read.csv("intensity.csv", row.names=1)          # 已是蛋白×样本
meta <- read.csv("samples.csv")                        # sample,group
stopifnot(colnames(mat)==meta$sample)
eset <- log2(mat + 1)                                  # 或 log2(mat)，缺失后补
# 1) 过滤：每组至少 50% 样本有值（低覆盖蛋白删）
keep <- sapply(split(seq_along(meta$group), meta$group),
               function(i) rowSums(!is.na(eset[,i])) >= ceiling(length(i)*0.5))
eset <- eset[apply(keep,1,any),]
# 2) 归一化：列中位数对齐（TMT/LFQ 标准做法）；需要时 quantile
eset <- sweep(eset, 2, colMedians(eset, na.rm=TRUE), "-")
# 3) 缺失值：小比例(<5%)随机缺失→KNN/均值；左删(MNAR，低丰度)→
#    左移正态补值 (qnorm(0.01, mean(x), sd(x)) 或 QRILC)；两策略都跑做敏感性
# 4) limma 差异
design <- model.matrix(~0+group, meta); colnames(design) <- levels(meta$group)
fit <- eBayes(lmFit(eset, design))
res <- topTable(contrast..., number=Inf)               # contrast 用 contrasts= 命名传参!
```

**关键坑**：
- `topTable` 探针/蛋白 ID 在 **rownames**（历史血泪）
- `makeContrasts` 必须 `contrasts=` 命名传参
- MNAR 缺失不能简单删/均值补——低丰度蛋白会被系统性抬高；左移补值是保守选择，方法学要写明
- 富集用 clusterProfiler：蛋白符号先 `bitr` 映射 ENTREZID；`enrichGO/enrichKEGG` 前 `options(timeout=900)`
- 阈值：|log2FC| 阈值按数据分布定（常见 0.58=1.5倍 或 1），adj.P<0.05；不要硬搬转录组阈值

## 图（全部白底 bg="white"）

- 火山图：ggplot2，x=log2FC，y=-log10(adj.P)，显著点着色，Top10 基因标名，避免标签重叠（ggrepel 若有）
- 热图：pheatmap(z-score 行标准化)，聚类行，注释条=分组
- PCA：log2 矩阵 prcomp，ggplot 散点+椭圆，看批次
- 富集条形图/气泡图：clusterProfiler::dotplot 或手动 ggplot

## 蛋白-转录联合

- 取两平台共同基因 → 相关散点（Spearman）+ 象限图（转录↑蛋白↑ 等）
- 转录变化无蛋白变化 ≠ 无意义（翻译调控），解读分开写
- WGCNA 可做蛋白共表达模块（转录组同法）

## 结果目录

`workspace/default/<项目>/proteomics/{data,figures,report}`；报告含：样本量/过滤数/补值策略/差异蛋白数/富集 top 通路/局限。
