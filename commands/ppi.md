---
description: 蛋白互作（PPI）网络分析 — STRING 网络构建/枢纽/模块/出图
argument-hint: <基因列表或分析需求，如：IL6 TNF IL1B NLRP3 的互作网络>
---

PPI 分析：$ARGUMENTS

按 bio-research-agent 插件 ppi-analyzer skill 执行：

1. `mcp__biomed__string_network` 拉网络（默认 min_score=0.4；机制图用 0.7；可 add_nodes 扩展找模块），核对 n_nodes 是否等于输入数；
2. 枢纽：degree（工具返回）+ 介数/模块（R igraph 或 networkx），双指标分化要报告；
3. 可选与疾病靶点/差异基因取重叠；
4. 出图：Cytoscape 风格 igraph 配方（netpharm-pipeline.md §③④ + <网络图项目>/network_analysis.R），白底 300dpi；
5. 输出 nodes.csv/edges.csv/network.png + 中文小结（枢纽前10、模块、解读）。STRING score 是证据分不是结合强度，措辞注意。
