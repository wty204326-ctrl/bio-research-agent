---
name: ppi-analyzer
description: 蛋白互作（PPI）网络分析。多蛋白 STRING 互作网络构建、枢纽（degree/介数）排名、模块切分、add_nodes 网络扩展、与疾病靶点/差异基因取重叠、Cytoscape 风格网络图。当用户要：蛋白互作/PPI/互作网络/hub 蛋白/网络中心性/STRING 分析/机制网络图 时使用。
---

# 蛋白互作分析 ppi-analyzer

## 流程（五步）

1. **输入收集**：基因/蛋白符号列表（差异基因、交集靶点、文献清单、或让用户给）。人名缩写先统一为官方 gene symbol（`uniprot_lookup` 可查）。
2. **拉网络**：`mcp__biomed__string_network`
   - 常规 `min_score=0.4`（STRING 中等置信，默认分析档）；宽松 0.15（找弱关联）、严格 0.7（高置信，机制图用）
   - 输入 <2 个蛋白没有意义；**检查返回的 n_nodes 是否等于输入数**（STRING 会静默丢弃识别不了的符号，丢弃的要换别名重试）
   - 找隐藏模块：`add_nodes=10~20` 让 STRING 补充高置信伙伴
   - 小鼠加 `species="10090"`
3. **枢纽分析**：返回自带 degree 排名；介数中心性/接近中心性/模块检测（louvain、greedy）用 R igraph（WSL `source ~/miniforge3/bin/activate rna`）或 Python networkx（WSL dock env）——度最高≠介数最高的分化要报告（先例：AKT1 介数最高而 IL6 度最高）。
4. **重叠**：与疾病靶点（`opentargets_disease_targets`）、差异基因列表取交集，标进节点表。
5. **出图**：Cytoscape 风格网络图——复用已验证 igraph 配方与现成脚本 `<你的 igraph 网络图脚本.R>`（配方细节见 bio-runner 的 references/netpharm-pipeline.md §③④：菱形=重点节点手动 polygon、text() 手动标签、graphopt charge=-0.35；边粗细∝score）。**纯白背景**。

## 输出规范

- `nodes.csv`：gene, degree, betweenness(如有), module(如有), 是否输入节点, 是否疾病重叠
- `edges.csv`：a, b, score
- `network.png`（白底，300dpi）+ 中文小结：枢纽前 10、模块划分、生物学解读（3-5 句）

## 边界

- STRING score 是证据整合分（0-1），不是结合强度——解读时不要说"结合力强"。
- 互作数据是**预测/文献证据**，不是本实验验证；结论措辞用"提示/支持"。
- 大列表（>300）分批拉或只保留高分管边，防图糊。
