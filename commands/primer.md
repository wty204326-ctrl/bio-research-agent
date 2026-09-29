---
description: PCR 引物设计 — primer3（qPCR/常规，Tm/GC/发夹/产物）
argument-hint: <模板序列文件+要求，如：gene.fa 设计 qPCR 引物 100-180bp>
---

引物设计：$ARGUMENTS

用 bench-quant skill 的 `scripts/primer_design.py`（primer3-py 已装）：
```
python scripts/primer_design.py --seq gene.fa --qpcr --product-min 100 --product-max 180 --pairs 5
```
- FASTA 或纯文本序列均可；--target start,length 可强制产物覆盖目标区；
- 输出前 N 对：序列/Tm(目标±3)/GC(40-60)/自互补/发夹/产物大小 → primers.csv；
- 呈现时给推荐对（Tm 接近、自互补低）+ 跨外显子提醒（qPCR 需用户确认基因组结构）。
