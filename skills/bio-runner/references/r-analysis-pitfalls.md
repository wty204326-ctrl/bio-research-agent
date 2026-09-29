# R / 生信分析坑位速查（写 R 代码前扫一遍）

## 差异分析

- **`topTable()` 的探针 ID 在 rownames，不在 `$probe` 列**——`tt$probe` 静默返回 NULL → 交集恒空 → 下游全崩（曾浪费数轮调试）。诊断打印要警惕"看起来正常"。
- limma `makeContrasts` 位置参数走 NSE，必须 `contrasts=` 命名传参。
- BH 校正饱和（min adj.P ≈ 1，如 13v21 全血 ICU 队列）属**数据属性非分析错误** → nominal 层 + rank 层（fgsea 全 t 值）双轨并如实披露。
- 芯片注释入流水线（解析 GPL annot.gz），不依赖历史 results 文件；设计矩阵放协变量（品系/批次），注释率要报告。
- 探针→基因：多探针取 max |logFC| 或平均，方法写明。

## 机器学习（防审稿人红线）

- **特征泄漏**：特征筛选必须嵌套在每折训练集内（嵌套 CV）。
- 跨平台验证：用**训练集均值/SD** 做 z-score；LASSO 概率可能整体塌缩到 ~0——AUC 只代表排序能力，不可当诊断概率，如实写。
- 样本量小（<50）报告 CV 方差与重复次数（5折×5次）。

## scRNA / Seurat

- Seurat v5 `FetchData` 用 **`layer=`** 不是 `slot=`（后者硬报错）。
- `AggregateExpression` 把组名下划线换破折号（名称变形）→ 用字母数字键匹配样本；`slot=`+`layer=` 双传参会报 formal argument matched twice。
- Assay5 对象 merge 在低内存必 OOM（std::bad_alloc）→ **矩阵层合并**：逐样本 counts 稀疏矩阵 cbind + 手工拼 meta + 一次 CreateSeuratObject；两阶段：stage1 逐样本过滤下采样存 rds，stage2 全新会话合并。
- 确定性下采样（seed 42、每样本固定 N）方法学必须披露。
- babelgene 鼠→人 ortholog：**输入鼠源时 `human=FALSE`**（该参数表示输入物种；传反会假性大面积 unmapped）。人鼠结果一致性要用正式映射验证。
- 逐步骤独立 Rscript 会话比 run.R 链式稳（自动重跑依赖 + 退出码失真）。
- DoubletFinder 大样本（60k 细胞）内存风险，可关或 standalone。
- scRNA 流程 config.yaml 中文注释在 GBK locale 下解析成 NULL（所有步骤静默 OFF）→ 配置文件纯 ASCII。

## 编码与 IO

- python `utf-8-sig` 写的 csv，R `read.csv` 必须加 `fileEncoding="UTF-8-BOM"`，否则首列名带 \ufeff、`$` 取列得 NULL（交集全零假象）。
- R 脚本文件头 BOM → "unexpected invalid token"，剥除再跑。
- 调色板数量 ≥ 簇数（动态扩色）。
- `grep` 模式含 `$` 用 `grep -F`（否则当行尾锚点）。
- `rm()` 删列表元素用 `rm(list=)` 或 `objs[i] <- NULL`。
- R `topTable` 输出列名是 `AveExpr`（非 aveExpr）。

## 富集

- R 脚本开头 **`options(timeout=900)`**（enrichKEGG 默认 60s 超时，KEGG REST 常慢）。
- fgsea 的 P 值列名是小写 `pval` 不是 `PValue`。
- msigdbr 26.x KEGG 子集名 `CP:KEGG_LEGACY`。
- GOA gaf 文件按物种过滤前**先抽样验证实际文件**（DB 列构成会变，2026 版 GO:0006979 全为 UniProtKB）。

## 绘图（强制规范）

- **所有图纯白背景**：ggsave/png 一律 `bg="white"`；透明 PNG 必须铺白（PIL 铺白法）；这是用户红线。
- PNG 设备无中文字体（变方框）→ 图内文字用英文；必须中文时 showtext 挂 `/mnt/c/Windows/Fonts/msyh.ttc` 或装 fonts-noto-cjk。
- UMAP/tSNE 用细胞类型标注（数字版留 *_numbered 备份）。
