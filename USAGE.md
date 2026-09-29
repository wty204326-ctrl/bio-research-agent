# bio-research-agent 使用手册（v0.5.0）

个人生物医药科研 agent：10 个 skills / 24 个命令 / 14 个数据库 MCP 工具。

## 一、安装

**方式 A：本地市场（开发/个人机）**
1. ZCode → 插件市场 → 添加 → 添加插件市场，粘贴本仓库克隆目录
2. 个人 → 对应市场 → 「生物医药科研助手」→ 安装
3. 设置 → 插件 里管理开关

装好后新开任务试：`/chem 槲皮素`（几秒返回性质+靶点即全链路通）。

**更新**：市场源刷新 → 插件 → 更新。

## 二、24 个命令速查（按场景）

**文献情报**：/lit 检索筛选调研 · /askpdf 本地 PDF 库问答 · /geo GEO 数据集检索
**化合物与靶点**：/chem 秒查性质/靶点/互作 · /admet 成药性（可接本地 ADMET 服务）· /ppi 互作网络
**干实验**：/bio 转录组 · /proteo 蛋白组 · /dock 分子对接 · /scrna 单细胞 · /mr 孟德尔随机化
**湿实验**：/wb WB 灰度 · /qpcr ΔΔCt · /elisa 4PL · /ihc IHC/IF · /colony 克隆计数 · /primer 引物 · /samplesize 样本量 · /pk 药代 NCA
**图与报告**：/plot R 出版图 · /fig 位图裁拼 · /report docx 报告
**法规与写作**：/gcp 中国 GCP 条款 · /plain 中译中

## 三、自然语言触发

不必记命令——skills 按关键词自动挂载：说"查文献/帮我调研"→lit-scout；"这条 WB 帮我定量"→bench-quant；"中译中一下"→plain-rewriter；"新版 GCP 数据治理"→gcp-advisor。

## 四、可接的本地依赖（全部可选）

| 依赖 | 何时需要 |
|---|---|
| 本地 ADMET 预测服务（默认 127.0.0.1:8100，POST /api/predict {"smiles":...}） | /admet |
| WSL（conda：DESeq2/limma/clusterProfiler 等） | /bio /proteo /dock /mr |
| Windows R ≥4.5 | /scrna /plot |
| GraphPad Prism | .pzfx 双击续作（samples/ 有验收样例） |
| Python ≥3.10 + PIL/numpy/scipy/pandas/cv2/statsmodels/primer3-py | 湿实验全家桶 |

## 五、典型工作流

1. 网药一条龙：/chem → 靶点采集 → /geo 找数据 → /bio 差异 → /ppi 网络 → /dock 对接 → /admet → /report
2. WB 到 GraphPad：发图 → 校验 ROI → results+figure → "出 GraphPad 文件" → .pzfx 在 Prism 续作
3. 开题机制链：/ppi → /mr 因果 → /scrna 验证 → /plain 中译中

## 六、常见问题

- 图一律白底（内置）
- EuropePMC 偶发 503 → 自动换 PubMed+OpenAlex 双库
- NMPA 原文抓取用 web_reader 类工具（WebFetch 会 412）
- scRNA config 必须纯 ASCII
- WSL 长任务 setsid nohup 脱离 + 轮询；Windows 下后台执行
