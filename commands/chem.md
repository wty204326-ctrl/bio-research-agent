---
description: 快查化合物/靶点/互作/疾病靶点（PubChem/ChEMBL/STRING/UniProt/OpenTargets）
argument-hint: <化合物名或基因名，如：槲皮素 / IL6 / 急性肺损伤的靶点>
---

快查（只查不跑计算）：$ARGUMENTS

用 `biomed` MCP 工具直查：

- 化合物 → `mcp__biomed__pubchem_compound`（性质）+ `mcp__biomed__chembl_molecule`（CHEMBL ID/临床阶段）；要活性再加 `mcp__biomed__chembl_activities`
- 基因/蛋白 → `mcp__biomed__uniprot_lookup` + `mcp__biomed__string_interactions`
- 疾病 → `mcp__biomed__opentargets_search` 找 MONDO ID → `mcp__biomed__opentargets_disease_targets`

输出：中文小结表格 + 数据来源与检索日期。天然产物查不到时按工具描述里的兜底建议换 SMILES/InChIKey/垂钓通道，并如实说明收录情况。
