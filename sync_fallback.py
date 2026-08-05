#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 fan_data.json 的内容自动注入两个 HTML 文件的 const FALLBACK_DATA = {...}; 块。
消除"手动同步内联兜底数据经常漏掉"的环节 —— 让看板在 file:// 直接打开时
也能显示最新粉丝数（fetch 失败回退到 FALLBACK 时不再陈旧）。

用法: python3 sync_fallback.py
"""
import json, os, re, sys

SRC = os.path.dirname(os.path.abspath(__file__))
FAN = os.path.join(SRC, "fan_data.json")
FILES = [
    os.path.join(SRC, "Gangstar运营看板.html"),
    os.path.join(SRC, "Gangstar运营看板_分享版.html"),
]

MARK = "const FALLBACK_DATA = "

def load_fan():
    with open(FAN, encoding="utf-8") as f:
        return json.load(f)

def replace_block(html, data):
    i = html.find(MARK)
    if i < 0:
        raise RuntimeError("未找到 const FALLBACK_DATA = 块")
    # 从 MARK 之后的 '{' 起做括号配对，找到最外层 '}' 的结尾
    j = html.index("{", i)
    depth = 0
    k = j
    while k < len(html):
        c = html[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    # k 指向最外层对象的 '}'；其后紧跟一个 ';'
    end = k + 1
    while end < len(html) and html[end] == ";":
        end += 1
    new_block = MARK + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    return html[:i] + new_block + html[end:]

def main():
    data = load_fan()
    stamp = data.get("updated_at", "?")
    for fp in FILES:
        if not os.path.exists(fp):
            print("SKIP (missing)", fp); continue
        with open(fp, encoding="utf-8") as f:
            html = f.read()
        out = replace_block(html, data)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"✅ 已同步 FALLBACK -> {os.path.basename(fp)} (updated_at={stamp})")
    print("DONE")

if __name__ == "__main__":
    main()
