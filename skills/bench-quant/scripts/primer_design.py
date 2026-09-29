#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引物设计（primer3-py 封装）：qPCR/常规 PCR 用
用法:
  python primer_design.py --seq template.txt --product-min 100 --product-max 200 --opt-tm 60 --pairs 5
  python primer_design.py --seq gene.fa --target 201,100   # 目标区间起始,长度（产物须覆盖）
输入: FASTA 或纯文本序列（自动去空白/非 ATGCN）
输出: 前 N 个引物对（序列/长度/Tm/GC/自互补/发夹/产物大小），CSV + 屏显
"""
import argparse
import pandas as pd
import primer3

def read_seq(path):
    seq = []
    for line in open(path, encoding="utf-8-sig"):
        if line.startswith(">"):
            continue
        seq.append("".join(c for c in line.strip().upper() if c in "ATGCN"))
    return "".join(seq)

def main(a):
    seq = read_seq(a.seq)
    if len(seq) < a.product_min + 40:
        raise SystemExit(f"序列太短({len(seq)}bp)，无法设计 {a.product_min}-{a.product_max}bp 产物")
    spec = {
        "SEQUENCE_TEMPLATE": seq,
        "PRIMER_TASK": "generic",
        "PRIMER_PICK_LEFT_PRIMER": 1,
        "PRIMER_PICK_RIGHT_PRIMER": 1,
        "PRIMER_PICK_INTERNAL_OLIGO": 0,
        "PRIMER_MIN_SIZE": 18, "PRIMER_OPT_SIZE": 21, "PRIMER_MAX_SIZE": 24,
        "PRIMER_OPT_TM": a.opt_tm, "PRIMER_MIN_TM": a.opt_tm - 3, "PRIMER_MAX_TM": a.opt_tm + 3,
        "PRIMER_MIN_GC": 40, "PRIMER_MAX_GC": 60,
        "PRIMER_MAX_SELF_ANY": 8, "PRIMER_MAX_SELF_END": 3,
        "PRIMER_MAX_HAIRPIN": 40 if a.qpcr else 47,
        "PRIMER_PAIR_MAX_COMPL_ANY": 8,
        "PRIMER_PRODUCT_SIZE_RANGE": [[a.product_min, a.product_max]],
    }
    if a.target:
        s, ln = (int(x) for x in a.target.split(","))
        spec["SEQUENCE_TARGET"] = [s, ln]
    if a.qpcr:
        spec["PRIMER_OPT_SIZE"] = 20
        spec["PRIMER_PRODUCT_SIZE_RANGE"] = [[max(70, a.product_min), min(200, a.product_max)]]
        spec["PRIMER_MAX_POLY_X"] = 3
    res = primer3.bindings.design_primers(spec, {})
    n = res.get("PRIMER_PAIR_NUM_RETURNED", 0)
    if not n:
        raise SystemExit("primer3 未找到合格引物对：放宽 --product-min/--max、降低 --opt-tm 或检查序列质量（N 比例）")
    rows = []
    for i in range(min(n, a.pairs)):
        rows.append(dict(
            pair=i + 1,
            forward=res[f"PRIMER_LEFT_{i}_SEQUENCE"],
            forward_tm=round(res[f"PRIMER_LEFT_{i}_TM"], 1),
            forward_gc=round(res[f"PRIMER_LEFT_{i}_GC_PERCENT"], 0),
            reverse=res[f"PRIMER_RIGHT_{i}_SEQUENCE"],
            reverse_tm=round(res[f"PRIMER_RIGHT_{i}_TM"], 1),
            reverse_gc=round(res[f"PRIMER_RIGHT_{i}_GC_PERCENT"], 0),
            product_size=res[f"PRIMER_PAIR_{i}_PRODUCT_SIZE"],
            self_any_fwd=res[f"PRIMER_LEFT_{i}_SELF_ANY_TH"] if f"PRIMER_LEFT_{i}_SELF_ANY_TH" in res else res.get(f"PRIMER_LEFT_{i}_SELF_ANY"),
            hairpin_fwd=res.get(f"PRIMER_LEFT_{i}_HAIRPIN_TH"),
            pair_complany=res.get(f"PRIMER_PAIR_{i}_COMPL_ANY_TH"),
        ))
    df = pd.DataFrame(rows)
    df.to_csv(a.out, index=False, encoding="utf-8-sig")
    print(df.to_string(index=False))
    print(f"[ok] {len(rows)} 对引物 → {a.out}（模板 {len(seq)}bp；Tm 目标 {a.opt_tm}±3）")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seq", required=True)
    ap.add_argument("--product-min", type=int, default=100)
    ap.add_argument("--product-max", type=int, default=200)
    ap.add_argument("--opt-tm", type=float, default=60)
    ap.add_argument("--pairs", type=int, default=5)
    ap.add_argument("--target", default=None, help="start,length 产物须覆盖的目标区间")
    ap.add_argument("--qpcr", action="store_true", help="qPCR 模式（70-200bp、严格 poly-x）")
    ap.add_argument("--out", default="primers.csv")
    main(ap.parse_args())
