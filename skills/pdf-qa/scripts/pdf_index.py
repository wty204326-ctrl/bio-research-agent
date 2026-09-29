#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地 PDF 库索引器（TF-IDF，零外部服务）
用法: python pdf_index.py --dir "C:/path/to/pdfs" --out index.json [--glob "*.pdf"] [--max-chars 700]
输出 index.json：{files:[{path,pages}], chunks:[{file,page,text}], df:{term:文档频率}}
之后用 pdf_query.py 检索。增量：重复运行全量重建（几百篇内秒级-分钟级）。
"""
import argparse, glob, json, math, os, re
import fitz  # PyMuPDF

WORD = re.compile(r"[a-z0-9]{2,}")
CJK = re.compile(r"[\u4e00-\u9fff]")

def tokenize(text):
    toks = WORD.findall(text.lower())
    cjk = "".join(CJK.findall(text))
    toks += [cjk[i:i + 2] for i in range(len(cjk) - 1)]  # 中文二元
    return toks

def chunks_of(page_text, max_chars):
    """按段落/句子切块，块间留 80 字重叠线索（页内顺序拼接）"""
    text = re.sub(r"\s+", " ", page_text).strip()
    out, start = [], 0
    while start < len(text):
        piece = text[start:start + max_chars]
        if start + max_chars < len(text):
            cut = max(piece.rfind(". "), piece.rfind("。"), piece.rfind(" "))
            if cut > max_chars * 0.5:
                piece = piece[:cut + 1]
        out.append(piece.strip())
        start += len(piece)
    return [c for c in out if len(c) > 40]

def main(a):
    files = sorted(set(sum([glob.glob(os.path.join(a.dir, "**", g), recursive=True) for g in a.glob_list], [])))
    files = [f for f in files if os.path.getsize(f) > 1e3]
    if not files:
        raise SystemExit(f"{a.dir} 下没找到 PDF")
    index = {"files": [], "chunks": [], "df": {}}
    seen_docs = set()
    for i, f in enumerate(files, 1):
        try:
            doc = fitz.open(f)
            npages = len(doc)
            for pno in range(npages):
                for ch in chunks_of(doc[pno].get_text(), a.max_chars):
                    toks = set(tokenize(ch))
                    index["chunks"].append({"file": os.path.basename(f), "path": f, "page": pno + 1, "text": ch})
                    for t in toks:
                        if len(t) > 1:
                            index["df"][t] = index["df"].get(t, 0) + 1
            doc.close()
            index["files"].append({"path": f, "pages": npages})
            print(f"[{i}/{len(files)}] {os.path.basename(f)}: {npages}p")
        except Exception as e:
            print(f"[skip] {f}: {e}")
    n_docs = len(index["files"])
    index["df"] = {t: df for t, df in index["df"].items() if df >= 2 or n_docs < 5}
    json.dump(index, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[ok] {len(index['files'])} 个 PDF / {len(index['chunks'])} 块 / 词表 {len(index['df'])} -> {a.out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", default="pdf_index.json")
    ap.add_argument("--glob", dest="glob_list", action="append", default=["*.pdf"])
    ap.add_argument("--max-chars", type=int, default=700)
    main(ap.parse_args())
