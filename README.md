# bio-research-agent 生物医药科研助手

一个面向生物医药科研的 [ZCode](https://z.ai) 插件：**10 个 skills / 24 个斜杠命令 / 14 个生物医药数据库 MCP 工具**，覆盖文献、干实验、湿实验、法规与写作的一条龙科研辅助。

## 它能做什么

| 模块 | 能力 |
|---|---|
| **文献** | PubMed/OpenAlex 检索、批量筛选（>20 篇自动扇出轻量模型）、结构化摘要、本地 PDF 库问答（带页码引用）、GEO 数据集检索 |
| **化合物/靶点** | PubChem 性质、ChEMBL 活性靶点、结构相似性垂钓、STRING 单蛋白/多蛋白互作网络、UniProt、OpenTargets 疾病靶点 |
| **干实验** | 转录组差异（DESeq2/limma）、蛋白组学（LFQ/TMT/DIA→limma）、网络药理学六步管线、分子对接（Vina）、单细胞（驱动 28 步 Seurat 流水线）、孟德尔随机化 |
| **湿实验定量** | WB 条带灰度定量、qPCR ΔΔCt、ELISA 4PL 标准曲线、IHC(DAB)/IF 图像定量、克隆计数、引物设计（primer3）、样本量/效能、**药代动力学 NCA**（Cmax/AUC/t½/CL/Vd + 一房室拟合） |
| **图与报告** | GraphPad 原生 .pzfx 生成、位图裁拼/面板字母/比例尺、docx 报告 |
| **法规与写作** | 中国 2026 版 GCP 条款解读（公告 2026 年第 50 号）、中译中三级简化改写 |

## 安装

1. 克隆本仓库
2. ZCode → 插件市场 → 添加 → 添加插件市场 → 粘贴仓库目录
3. 个人 → bio-research-agent → 安装
4. 新任务发 `/chem quercetin` 验证

湿实验脚本需要 Python ≥3.10 与 `pillow numpy scipy pandas opencv-python statsmodels primer3-py matplotlib openpyxl`；干实验建议 WSL + conda（DESeq2/limma/clusterProfiler 等）。详见 [USAGE.md](USAGE.md)。

## 验证状态（诚实清单）

- MCP 12/14 工具真实 API 验证（admet 需自备本地服务；EuropePMC 标备用）
- WB 合成膜回收误差 <3%；ELISA ≤5%；qPCR 数学一致性；IHC 面积误差 <1%、核检出 89/90；克隆 42→39（重叠合并为已知限制）；样本量对齐教科书基准；引物 Tm 目标 ±0.1；PK 合成数据 AUC 误差 ≤1%、CL/Vd ≤4.4%；pdf-qa 真实文献带页码命中
- .pzfx 为数据表模式，Prism 兼容性请用 samples/ 样例自验

## 免责与边界

- 预测/定量结果仅供研究参考，不构成医疗建议；ADMET 数值是模型预测非实验值。
- 各数据库均为官方公开接口，请遵守各自使用条款与速率限制。
- 法规解读给通行理解，具体项目合规请咨询机构/伦理委员会。

## License

MIT
