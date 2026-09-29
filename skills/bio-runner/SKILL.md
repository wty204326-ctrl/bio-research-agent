---
name: bio-runner
description: 生信+网络药理学执行器。转录组差异分析(DESeq2/limma)、单细胞scRNA(Seurat)、富集分析(GO/KEGG/GSEA)、机器学习建模；网络药理学全流程(成分靶点挖掘→疾病靶点→交集Venn→PPI网络→分子对接docking)；化合物/靶点/互作快查。当用户要：差异分析/转录组/单细胞/scRNA/GEO数据/富集/网络药理学/靶点预测/分子对接/docking/查化合物性质 时使用。
---

# 生信+网药执行器 bio-runner

三大通道。**执行 WSL 任务前必读对应 references 文件**——里面是本项目机器验证过的管线与血泪坑，不读会重蹈覆辙。

## 0. 快查通道（只查不跑，秒回）

化合物/靶点/互作直接调 `biomed` MCP 工具：

| 问题 | 工具 |
|---|---|
| 化合物性质（MW/LogP/TPSA/SMILES/InChIKey） | `mcp__biomed__pubchem_compound` |
| 化合物 CHEMBL ID / 临床阶段 | `mcp__biomed__chembl_molecule` |
| 化合物已知活性靶点 | `mcp__biomed__chembl_activities` |
| 结构相似分子（垂钓用） | `mcp__biomed__chembl_similarity` |
| 蛋白互作伙伴（PPI） | `mcp__biomed__string_interactions` |
| 蛋白功能/基因符号 | `mcp__biomed__uniprot_lookup` |
| 疾病 MONDO ID | `mcp__biomed__opentargets_search` |
| 疾病关联靶点 | `mcp__biomed__opentargets_disease_targets` |

已知锚点：急性肺损伤=MONDO_0015796、ARDS=MONDO_0006502；绿原酸=CHEMBL284616。

## 1. 网络药理学流水线（六步）

详细参数、API 坑、已验证结论：**执行前必读 references/netpharm-pipeline.md**

①成分靶点（ChEMBL 双通道活性 + 相似性垂钓 ≥50% + 代谢物替代 + 文献补充；SwissTargetPrediction/STITCH 已死勿试）
②疾病靶点（OpenTargets ≥0.05；防单库偏倚）
③交集 Venn → ④STRING PPI + degree/介数枢纽 → ⑤clusterProfiler 富集 → ⑥分子对接（references/docking-manual.md）。

## 2. 转录组 / 单细胞 / 蛋白组学

- **单细胞（scRNA/scRNA-seq/Seurat）不在本 skill**——一律走 `scrna-runner`（驱动用户 Desktop 的 scRNA_workflow，Windows R，见其 references/scrna-workflow.md）。
- bulk 转录组环境：WSL conda `rna`（DESeq2/limma/clusterProfiler/glmnet/xgboost 全家桶，13 包已验证）。
- ⚠️ **任何 WSL 命令执行前先读 references/wsl-ops.md**（base64 传脚本、setsid nohup、VM 崩溃排查——全是本机血泪）。
- R 代码坑（topTable/FetchData/babelgene/编码等）：**references/r-analysis-pitfalls.md** 写代码前扫一遍。
- **蛋白组学**（LFQ/TMT/DIA 通用强度矩阵 → limma 差异 → 火山/热图/富集）：**references/proteomics-manual.md**，含 MaxQuant 过滤、MNAR 补值、归一化要点。
- 方法学红线（防审稿人）：特征选择必须嵌套在 CV 折内；跨平台验证用训练集 z-score；BH 饱和时 nominal+rank 双轨如实披露；确定性下采样要写进方法。

## 3. 执行策略

- 计算任务直接 Bash 顺序执行，**不用子代理**（WSL 状态机握在主会话手里最稳）。
- 长任务（>2 分钟）：setsid nohup 完全脱离 + Windows 侧短命令轮询日志（wsl.exe 附着会话 ~2 分钟即被回收）。
- 结果解读/报告：主模型写。批量文献补充检索才用 Flash 子代理（见 lit-scout §3）。
- 结果目录规范：`workspace/default/<项目名>/{data,figures,report,wsl}`。
- **所有图纯白背景**（ggsave/png 一律 `bg="white"`，禁透明 PNG——用户红线）。
- 对接/GEO 下载等长 IO：分段并行 + 逐段字节校验（见 wsl-ops.md 网络）。

## 4. 可复用现成脚本（复制改造，勿从零写）

- 网络药理学靶点检索/Venn/PPI/富集：`<你的网药脚本目录>/np_fetch2.py、np_analyze.py、np_enrich.R`
- 对接矩阵（36 组架构）：`<对接矩阵脚本.py（参考思路，自备）>`、`<你的项目目录>/wsl/run_phn_dock.py`
- 化合物-靶点 Cytoscape 风格网络图（igraph 配方）：`<你的 igraph 网络图脚本.R>`
- 制备流水线 01-06：`<制备流水线脚本目录>/`（Windows 侧备份）
