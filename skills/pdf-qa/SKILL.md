---
name: pdf-qa
description: 本地 PDF 文献库问答。对指定文件夹建 TF-IDF 索引（PyMuPDF 提取，带页码），检索问题相关原文块后由主模型精读作答。当用户要：问我的PDF库里/在这些文献里找/我存的那篇讲的什么/基于本地文献回答 时使用。
---

# 本地 PDF 库问答 pdf-qa

两脚本在本 skill `scripts/`（Windows Python，PyMuPDF 已装）。

## 流程

1. **建索引**（一个库只建一次，之后直接查询）：
   ```
   python scripts/pdf_index.py --dir "C:/Users\<you>/Research/某个文献夹" --out <库目录>/pdf_index.json
   ```
   递归找 PDF；输出块=文件+页码+文本（~700 字/块，中文按二元切词）。
2. **检索**：
   ```
   python scripts/pdf_query.py --index <库目录>/pdf_index.json --q "英文关键词" --k 6
   ```
   返回 top-k 原文块（含页码与路径）。查询词用**英文**（PDF 正文多为英文）；中文问题先翻译成关键词。
3. **作答**：主模型读 top-k 块原文 → 回答用户问题，**每条论断标注（文件名 p页码）**；必要时 Read 对应 PDF 页深挖。
4. 块里找不到 → 换关键词再检索一次；仍无 → 如实说库里没有，不脑补。

## 纪律

- 回答只用检索到的原文支撑；页码引用必须真实来自检索结果。
- 大库（几百篇）索引分钟级，建议放后台跑。
- 用户已知库：GSTP/GSTO 文献合集 67 篇（位置问用户或查 Research 目录）。

## 分工

在线文献检索 → lit-scout；本地已下载 PDF 的问题 → 本 skill。
