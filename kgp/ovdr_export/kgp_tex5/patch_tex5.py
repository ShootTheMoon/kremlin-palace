# -*- coding: utf-8 -*-
r"""swap_tex5_NN.json 을 저장된 .ovdrjm 에 guid 단위로 국소 치환한다 (TextureId 만).

파일 전체를 다시 쓰지 않는다(Studio 서식 유지). 각 파츠 노드 { } 안에서 TextureId 가 정확히 1번
매치되지 않으면 아무것도 쓰지 않고 멈춘다. 먼저 overdare_save → 백업 → 이것 → overdare_apply → save.

    python patch_tex5.py
"""
import glob
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = r"C:\Work\onlyonetap\onlyoneshot.ovdrjm"

ups = []
for f in sorted(glob.glob(os.path.join(HERE, "swap_tex5_[0-9][0-9].json"))):
    ups += json.load(io.open(f, encoding="utf-8"))
print("updates:", len(ups))

data = open(PRJ, "rb").read()
raw = data.decode("utf-16-le")
bom = raw[0] == "\ufeff"
if bom:
    raw = raw[1:]


def span(s, guid):
    tok = '"' + guid + '"'
    if s.count(tok) != 1:
        raise SystemExit("guid not unique: %s (%d)" % (guid, s.count(tok)))
    i = s.index(tok)
    a = s.rindex("{", 0, i)
    depth, j, instr, esc = 0, a, False, False
    while True:
        ch = s[j]
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        else:
            if ch == '"':
                instr = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return a, j + 1
        j += 1


R_TEX = re.compile(r'("TextureId":\s*")[^"]*(")')
pieces = []
for u in ups:
    a, b = span(raw, u["guid"])
    node = raw[a:b]
    new, n = R_TEX.subn(lambda m: m.group(1) + u["props"]["TextureId"] + m.group(2), node)
    if n != 1:
        raise SystemExit("TextureId matched %d times in %s" % (n, u["guid"]))
    pieces.append((a, b, new))

pieces.sort()
out, prev = [], 0
for a, b, node in pieces:
    assert a >= prev, "overlap"
    out.append(raw[prev:a])
    out.append(node)
    prev = b
out.append(raw[prev:])
res = "".join(out)
json.loads(res)                                   # 깨지지 않았는지
open(PRJ, "wb").write((("\ufeff" if bom else "") + res).encode("utf-16-le"))
print("patched", len(pieces), "nodes ->", PRJ)
