# 网络药理学流水线手册（2026-09 实战验证版）

六步：成分靶点 → 疾病靶点 → 交集 → PPI/网络 → 富集 → 对接。
现成脚本：`<你的网药脚本目录>/`（np_fetch2.py / np_analyze.py / np_enrich.R / np_kegg.R）。

## ① 成分靶点（四通道合并）

1. **ChEMBL 直接活性**（MCP `chembl_activities` 已封装双通道）：
   - 通道A `activity.json?molecule_chembl_id=X&pchembl_value__gte=5`
   - 通道B `activity.json?molecule_chembl_id=X&standard_units=nM&standard_value__lte=10000`
   - 只用 A 会漏大量无 pChEMBL 值的记录，**必须双通道**。
   - ⚠️ `target_organism` 字段常为空，不可用于过滤人源：先收 target_chembl_id 再批量 `/target.json?target_chembl_id__in=a,b,c`（逗号批量优于 & 拼接）解析 organism + GENE_SYMBOL。
2. **相似性垂钓**（MCP `chembl_similarity`，SwissTargetPrediction 的替代）：SMILES + Tanimoto≥50%、top40，再逐个取相似分子的活性靶点。极慢（≈4 分钟/成分）→ 后台跑 + 逐成分缓存 JSON。糖苷 SMILES 编码可能报 500 → 改用 ChEMBL ID 绕开。
3. **代谢物替代**：糖苷口服必被肠道菌群代谢（示例大分子糖苷→淫羊藿苷 CHEMBL553204/宝藿苷I CHEMBL560116；示例糖苷→<代谢物 CHEMBL ID>），原型+代谢物靶点并集，报告中说明。
4. **文献通道**：逐基因标注来源文献（占坑文献尤其要核对）。

- TCMSP 可取 OB/DL 参考值（示例糖苷 MOL003305：OB 36.40 / DL 0.863）；⚠️ 糖苷立体异构体 InChIKey 要用 TCMSP 版本（PubChem 键可能查不到 CHEMBL6159931）。
- **已死服务（勿浪费时间）**：SwissTargetPrediction（新旧版均无结果表）、STITCH、PharmMapper（手工排队）。
- ⚠️ 化合物可能未被 ChEMBL 收录（示例大分子糖苷 无匹配）→ 走相似性垂钓 + 代谢物 + 文献。
- ⚠️ PubChem PUG-REST 不认某些天然产物俗名（"example glycoside" 404）→ 用 SMILES/_CID。分子量交叉核对（示例大分子糖苷 = C39H50O19, 822.3，曾被错记为 C33H40O19）。

## ② 疾病靶点

- **OpenTargets**（首选，免认证；MCP `opentargets_search` + `opentargets_disease_targets` 已封装）。
- 已知 MONDO：ALI=MONDO_0015796、ARDS=MONDO_0006502。
- ⚠️ 评分阈值 0.05 裁剪极狠（一个量级的缩减），阈值上下各留一版做敏感性。
- DisGeNET 要 token(401)、CTD 302 不可直取；RHOA/ROCK1/MYLK/TJP1 等屏障相关基因不在 OT 疾病库 → 单库偏倚用 GeneCards/文献补。

## ③④ 交集 + PPI + 网络

- STRING（MCP `string_interactions`，human=9606）；枢纽按 **degree + 介数中心性双指标**（曾出现介数最高 AKT1 而非 degree 最高 IL6 的分化）。
- igraph 网络图已验证配方（本机 igraph 2.x 坑）：
  - 注册自定义 vertex shape 会静默失败（菱形直接不画）→ plot 后用 polygon() 手动补画；
  - `layout_with_fr` 无 rescale 参数；`label.dist` 在 rescale=FALSE 坐标下失效 → 标签用 text() 手动放；
  - graphopt 布局 charge=-0.35；ggplot2 旧版用 `expand=c(0,x)` 不用 expansion()。
  - 现成脚本：`<你的 igraph 网络图脚本.R>`（化合物=菱形+靶点=圆形+手动标签）。

## ⑤ 富集

- clusterProfiler（conda rna env）；R 脚本开头 **`options(timeout=900)`**（enrichKEGG 默认 60s 必超时）。
- msigdbr 26.x KEGG 子集名是 `CP:KEGG_LEGACY`；fgsea 的 P 值列名是小写 `pval`。
- matplotlib-venn 三集合可能告警 "Bad circle positioning"（不影响出图）。

## ⑥ 对接

见同目录 docking-manual.md。

## 已验证科学结论（复用，勿重复踩）

- 校准参照（阳性对照锚点）：GRα×地塞米松 **−12.22** kcal/mol；西乐葆×PTGS2 −8.11；依托泊苷×TOP2A −11.81。
- **NLRP3 的 NACHT/ADP 口袋对接全线 −3.7~−4.5（含阳性药 MCC950）无区分力**——非其真实抑制剂位点；两个项目独立重复，NLRP3 对接结果只作局限披露。
- 常用校准 PDB 示例：6GSS、1DNU、5GWK（5GWK 共晶配体依托泊苷的残基名是 **EVP** 不是 ETF）。
- 糖苷原型 vs 苷元：示例糖苷(PHN)对接普遍优于苷元(PGN) → 原型为主要结合形式（项目结论，他项目需重验）。
