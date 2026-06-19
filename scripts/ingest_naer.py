# -*- coding: utf-8 -*-
"""接國教院樂詞網「兩岸一般名詞對照」官方詞庫（臺灣用語|大陸用語|英文）。
NAER 網站 SSL 憑證有瑕疵(Missing SKI)，公開政府資料一次性抓用免驗證 context 繞過。
官方對照 → hard，但同名異實假朋友(土豆/質量/水平…)一律跳過、GREY_ROUTE 降級、白名單保護。"""
import urllib.request as u
import ssl, io, zipfile, json, os, sys
import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.join(os.path.dirname(__file__), "..")
DICT = os.path.join(BASE, "references", "taiwanizer_dict.json")
SRCDIR = os.path.join(BASE, "references", "sources")
URL = "https://terms.naer.edu.tw/media/terms_data/custom_data/%E5%85%A9%E5%B2%B8%E4%B8%80%E8%88%AC%E5%90%8D%E8%A9%9E%E5%B0%8D%E7%85%A7.zip"

GREY_ROUTE = {"迭代", "優化", "數據", "用戶", "智能", "通過", "靠譜", "顏值", "內捲",
              "躺平", "變現", "痛點", "落地", "立馬", "渠道", "高端", "社區"}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def main():
    d = json.load(open(DICT, encoding="utf-8"))
    whitelist = set(d.get("whitelist", []))
    false_friends = {e["zh"] for e in d.get("context", [])} | {"土豆", "質量", "水平", "窩心", "機車", "地道"}
    existing = {e["zh"] for e in d["hard"]} | {e["zh"] for e in d["grey"]} | false_friends

    raw = u.urlopen(u.Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=40, context=ctx).read()
    open(os.path.join(SRCDIR, "NAER_兩岸一般名詞對照.zip"), "wb").write(raw)
    z = zipfile.ZipFile(io.BytesIO(raw))
    xlsx_name = next(n for n in z.namelist() if n.lower().endswith(".xlsx"))
    wb = openpyxl.load_workbook(io.BytesIO(z.read(xlsx_name)), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    # 找表頭列（含「臺灣/大陸」的那列；前幾列可能是標題）
    hdr_idx, tw_i, zh_i = None, None, None
    for ri in range(min(6, len(rows))):
        cells = [str(c or "") for c in rows[ri]]
        ti = next((i for i, h in enumerate(cells) if "臺灣" in h or "台灣" in h), None)
        zi = next((i for i, h in enumerate(cells) if "大陸" in h), None)
        if ti is not None and zi is not None:
            hdr_idx, tw_i, zh_i = ri, ti, zi
            break
    if hdr_idx is None:
        print("找不到表頭，前兩列=", [list(r) for r in rows[:2]]); return

    import re
    # 已知方向反/語境易誤的，跳過（複製才是台灣詞、線路≠路線、民間大使存疑）
    DENY = {"複製", "線路", "民間大使"}

    def split_cell(s):
        return [p.strip() for p in re.split("[、，,;；/]", str(s or "")) if p.strip()]

    added, skip = 0, 0
    for row in rows[hdr_idx + 1:]:
        if not row or len(row) <= max(tw_i, zh_i):
            continue
        zh_list = split_cell(row[zh_i])        # 大陸用語可能多值，逐一拆開
        tw_list = split_cell(row[tw_i])         # 臺灣用語多值 → 當替代詞
        if not zh_list or not tw_list:
            continue
        for zh_w in zh_list:
            if (len(zh_w) < 2 or zh_w in DENY or zh_w in whitelist or zh_w in existing
                    or zh_w in tw_list or not any("一" <= c <= "鿿" for c in zh_w)):
                skip += 1
                continue
            tier = "grey" if zh_w in GREY_ROUTE else "hard"
            d[tier].append({"zh": zh_w, "tw": tw_list[:3],
                            "note": "兩岸一般名詞(國教院樂詞網)", "source": "naer"})
            existing.add(zh_w)
            added += 1

    d.setdefault("_meta", {})["last_naer_ingest"] = "2026-06-19 國教院樂詞網 兩岸一般名詞對照"
    json.dump(d, open(DICT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"NAER done: +{added}, skip {skip} | TOTAL hard={len(d['hard'])} grey={len(d['grey'])} "
          f"context={len(d.get('context', []))}")


if __name__ == "__main__":
    main()
