#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地 PDF 库检索：TF-IDF 余弦打分，返回 top-k 文本块（文件+页码）
用法: python pdf_query.py --index pdf_index.json --q "ferroptosis iron" --k 6
"""
import argparse, json, math, re
from collections import Counter

WORD = re.compile(r"[a-z0-9]{2,}")
CJK = re.compile(r"[\u4e00-\u9fff]")

def tokenize(text):
    toks = WORD.findall(text.lower())
    cjk = "".join(CJK.findall(text))
    toks += [cjk[i:i + 2] for i in range(len(cjk) - 1)]
    return toks

def main(a):
    idx = json.load(open(a.index, encoding="utf-8"))
    chunks, df, n_docs = idx["chunks"], idx["df"], max(len(idx["files"]), 1)
    q = tokenize(a.q)
    if not q:
        raise SystemExit("查询无有效词")
    idf = {t: math.log(1 + n_docs / (1 + df.get(t, 0))) for t in set(q)}
    scores = []
    for i, ch in enumerate(chunks):
        tf = Counter(t for t in tokenize(ch["text"]) if t in idf)
        if not tf:
            continue
        s = sum(idf[t] * (1 + math.log(c)) for t, c in tf.items())
        # 短块轻微惩罚（避免碎片刷分）
        s /= math.sqrt(1 + len(ch["text"]) / 2000)
        scores.append((s, i))
    scores.sort(reverse=True)
    for rank, (s, i) in enumerate(scores[: a.k], 1):
        ch = chunks[i]
        print(f"#{rank} [score {s:.2f}] {ch['file']} p{ch['page']}")
        print(f"   {ch['text'][:280]}{'...' if len(ch['text'])>280 else ''}")
        print(f"   path: {ch['path']}")
    if not scores:
        print("无匹配块（换个问法或检查索引）")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", required=True)
    ap.add_argument("--q", required=True)
    ap.add_argument("--k", type=int, default=6)
    main(ap.parse_args())
