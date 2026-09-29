---
name: mr-analyzer
description: 孟德尔随机化（MR）分析。药物靶点MR设计（暴露/结局GWAS选源、工具变量、harmonize、IVW+敏感性、共定位coloc、功效门槛折算）。当用户要：孟德尔随机化/MR/两样本MR/因果推断/靶点MR/pQTL/eQTL/共定位/coloc 时使用。
---

# 孟德尔随机化 mr-analyzer

**执行前必读 references/mr-manual.md**——那是一个真实药物靶点 MR 项目全程实跑的资产清单：数据源可用性（哪些开放/哪些是空目录/哪些要申请）、下载与带宽坑、环境配置、现成脚本位置。

## 流程（药物靶点 MR 标准七步）

1. **设计**：暴露（靶点 pQTL/eQTL cis 窗口 ±1Mb）+ 结局（疾病/检验指标 GWAS）。先查 manual 的数据源表——**别用已确认下线/空目录的源**（GWAS Catalog 部分 accession FTP 为空、eQTL Catalogue API 410、OpenGWAS 要 JWT）。
2. **工具变量**：cis 显著 SNPs（5e-8 或 locus 内 top），clump r²<0.001；记录等位基因方向。
3. **harmonize**：效应等位对齐；**跨版本坐标（GRCh37/38）必须按位置重匹配**（Pazoki 文件两套坐标都有的坑）。
4. **估计**：IVW/Wald ratio + 加权中位数 + MR-Egger（敏感性）；单 SNP Wald。
5. **共定位**：coloc（conda rcoloc env，**mamba 必须 --override-channels**）；按位置去重后再跑（duplicated snps 报错）。
6. **功效门槛**：se ∝ 1/√病例数 → 检出给定 OR 需要的样本量（示例靶点案例：OR=1.2 需 pQTL~9600 例）。
7. **报告**：森林图（WSL matplotlib **纯英文**，中文豆腐块）+ 数据源清单 + 阴性也如实写。

## 环境速记

- 全部在 WSL：R 在 `~/miniforge3/envs/rna`（python 有 numpy/scipy/matplotlib **无 pandas**）；coloc 在 `rcoloc` env。
- MR 为**自实现 Python**（mr_analysis.py / acute_mr.py），不走 ieugwasr（无 JWT）。
- 现成脚本：`workspace/default/<你的 MR 脚本目录>/`；结果模板看你自己项目的 RESULTS.md。

## 纪律

- 方向与先验相反的"显著"结果默认按噪声处理，除非共定位支持。
- 量纲陷阱：非 SD 标度的表型（如 BBJ 肝酶）先校准再比效应量。
- 工具变量跨祖源不可移植（不同 panel 缺不同 SNP）——分开报告，不合并。
