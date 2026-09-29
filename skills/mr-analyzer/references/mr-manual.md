# MR 数据源与环境实战手册（真实药物靶点 MR 项目实跑沉淀）

## 数据源可用性（查过，直接用结论）

| 源 | 状态 | 用法 |
|---|---|---|
| FinnGen R12 | ✅ 开放 | `https://storage.googleapis.com/finngen-public-data-r12/summary_stats/release/finngen_R12_<端点>.gz`；manifest 在 `summary_stats/finngen_R12_manifest.tsv`（phenocode/num_cases/…）；beta=log-OR；GCS 下载 ~35MB/s |
| BBJ（DBCLS） | ✅ 开放 | `https://humandbs.dbcls.jp/files/hum0197/hum0197.v3.BBJ.<表型>.v1.zip`（~591MB/个，BOLT-LMM，ALLELE1=效应等位，GRCh37）；有 ALT/AST/GGT/ALP/TBil 无 ALB/LDH；限速 ~34KB/s/连接；疾病表型 beta 是风险差非 log-OR |
| eQTLGen 显著集 | ✅ 开放 | 308MB；注意同一基因可有方向相反的两簇工具 |
| GTEx | ⚠️ | API 只回显著结果；全量 allpairs 在 GCS 1.5-2GB tar；肝内低表达靶点可能无显著 cis-eQTL（曾实测某 21 TPM 靶点无信号，靶点要个案查） |
| 小样本 pQTL 开放版 | ✅ | GCST90059976(n=2917)、GCST90101050(n=997)、GCST90162182(卡塔尔 n=2935) |
| UKB-PPP pQTL (GWAS Catalog) | ❌ | GCST90433417 / GCST90247750 FTP 目录为空 |
| deCODE pQTL | ❌ 开放 | 只给申请表 download.decode.com |
| eQTL Catalogue API | ❌ | HTTP 410 下线 |
| GWAS Catalog 汇总 API | ❌ | 410 下线 |
| OpenGWAS/ieugwasr | ⚠️ | 需 JWT（本机没有）→ MR 自实现 |
| HOPE（中国汉族肝功 n=50,569） | ⚠️ | NGDC GVP000085 确认存在但 2022-01 起停自由下载，实名申请 |

## 下载与环境坑（血泪）

- 单连接国际带宽 ~1MB/s（EBI/RUG/DBCLS 一致）；**6 段并发 ~5MB/s**（`wsl/dl.sh` 已封装分段+大小+gzip 校验）；GCS 可 35MB/s。
- **绝不用 `curl | zcat | python` 流式管道**——断连静默产出截断结果（GGT 只扫 24 万行就"成功"过）。
- `setsid nohup` 后台任务活不过工具调用结束 → 用 run_in_background 或前台大 timeout。
- 远程 tabix 不可用（htslib 1.6 无 https；pysam 读 GCS 索引截断）→ FinnGen 整文件下载。
- `mamba install -n <env> -c conda-forge` 会拖进 defaults 挤掉 r-base → **必须 --override-channels**；WSL 无 gcc/make，R 包装 conda-forge 预编译（rcoloc env 就这么建的）。
- WSL matplotlib 无中文字体 → 图纯英文。
- `pkill -f` 模式含自身命令行会自杀 → `GCST9001340[5]` 写法。

## 方法学坑

- Pazoki 2021 harmonised 文件：ALP/GGT 无 rsID 只有位置；ALT 的 hm_rsid 同时含 GRCh38/GRCh37 两套坐标 → **按位置匹配**，列取错坐标错配。
- 该项目区域 GRCh38→37 偏移恒为 −232,529（Ensembl /map 实测）——其他区域要重新测。
- coloc 前按位置去重（同位点多等位基因多行 → duplicated snps 报错）。
- BBJ 肝酶非 SD 标度（≈Pazoki 的 4.8 倍）→ 折算后再比；BBJ 与欧洲用的工具变量可能根本不是同一 SNP。
- 功效门槛公式：se ∝ 1/√病例数 → 需要病例数 = (现病例数) × (se_需要/se_现有)²。
