# -*- coding: utf-8 -*-
"""接國教院樂詞網「兩岸對照名詞」49 領域檔（計算機/資訊/通信/電力/數學/醫學…）。
這些是 EN 錨定的 .ods，欄位＝中文名稱(台) / 中國大陸譯名(陸，且為簡體)。
處理：大陸簡體譯名 → 自建 OpenCC 字級 s2t 轉繁 → 只在「轉繁後 ≠ 台灣詞」時收（真兩岸差異）。
全部路由 grey（量大、只提示不自動改）。守門：假朋友/白名單/去重/反向 deny。
NAER SSL 瑕疵 → 免驗證 context。"""
import urllib.request as u
import ssl, io, zipfile, json, os, sys, re
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.join(os.path.dirname(__file__), "..")
DICT = os.path.join(BASE, "references", "taiwanizer_dict.json")
ZIPS = os.path.join(BASE, "_naer_zips.txt")
HOST = "https://terms.naer.edu.tw"
STCHARS = "https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/STCharacters.txt"

DENY = {"複製", "線路", "民間大使"}
# 只收寫作相關領域；跳過超冷門科學 jargon(材料/化學/海洋/動植物…會爆 5 萬條且拖慢)
ALLOW = ("計算機", "資訊", "通信", "醫學", "中醫", "中小學教科書", "音樂")
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
TBL = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"


def fetch(url, verify=False):
    c = None if verify else ctx
    return u.urlopen(u.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60, context=c).read()


def load_s2t():
    raw = fetch(STCHARS, verify=True).decode("utf-8", "replace")
    m = {}
    for line in raw.splitlines():
        if "\t" in line and not line.startswith("#"):
            s, t = line.split("\t", 1)
            m[s] = t.split()[0]        # 取第一個繁體變體
    return m


def s2t(text, M):
    return "".join(M.get(c, c) for c in text)


def strip_annot(s):
    s = re.sub(r"【.*?】|〔.*?〕|〈.*?〉|「.*?」|（.*?）|\(.*?\)|\[.*?\]", "", str(s or ""))
    return s.strip()


def split_cell(s):
    return [p.strip() for p in re.split(r"[、，,;；/]", str(s or "")) if p.strip()]


def find_cols(header):
    cells = [str(c or "") for c in header]
    ti = next((i for i, h in enumerate(cells)
               if "中文名稱" in h or "臺灣" in h or "台灣" in h
               or h.strip() in ("中文", "正體", "臺灣譯名")), None)
    zi = next((i for i, h in enumerate(cells) if "大陸" in h or "大陆" in h), None)
    return ti, zi


def rows_from_xlsx(b):
    wb = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    return [list(r) for r in wb.active.iter_rows(values_only=True)]


def rows_from_ods(b):
    root = ET.fromstring(zipfile.ZipFile(io.BytesIO(b)).read("content.xml"))
    out = []
    for table in root.iter(TBL + "table"):
        for row in table.iter(TBL + "table-row"):
            cells = []
            for cell in row.findall(TBL + "table-cell"):
                txt = "".join(cell.itertext()).strip()
                rep = int(cell.get(TBL + "number-columns-repeated", "1"))
                cells.extend([txt] * min(rep, 20))
            if any(cells):
                out.append(cells)
        break
    return out


def rows_from_docx(b):
    root = ET.fromstring(zipfile.ZipFile(io.BytesIO(b)).read("word/document.xml"))
    out = []
    for tr in root.iter(W + "tr"):
        cells = [("".join(t.text or "" for t in tc.iter(W + "t"))).strip()
                 for tc in tr.iter(W + "tc")]
        if any(cells):
            out.append(cells)
    return out


def extract_table(raw, depth=0):
    if depth > 3:
        return None
    try:
        z = zipfile.ZipFile(io.BytesIO(raw))
    except Exception:
        return None
    for name in z.namelist():
        b = z.read(name); low = name.lower()
        if low.endswith(".xlsx"): return ("xlsx", b)
        if low.endswith(".ods"): return ("ods", b)
        if low.endswith(".docx"): return ("docx", b)
        if low.endswith(".zip"):
            r = extract_table(b, depth + 1)
            if r: return r
    return None


def main():
    M = load_s2t()
    print(f"s2t 字表載入 {len(M)} 字")
    d = json.load(open(DICT, encoding="utf-8"))
    whitelist = set(d.get("whitelist", []))
    ff = {e["zh"] for e in d.get("context", [])} | {"土豆", "質量", "水平", "窩心", "機車", "地道"}
    existing = {e["zh"] for e in d["hard"]} | {e["zh"] for e in d["grey"]} | ff

    sci_mode = "--sci" in sys.argv      # 檢察官 ULTRA：收非寫作的冷僻科學領域
    src_tag = "naer-sci" if sci_mode else "naer-dom"
    links = [l.strip() for l in open(ZIPS, encoding="utf-8") if l.strip()]
    total, files_ok, files_skip = 0, 0, 0
    for link in links:
        uq = unquote(link)
        if "兩岸一般名詞對照" in uq or "音樂" in uq:   # 一般名詞已接、音樂系統性錯配跳過
            continue
        is_writing = any(k in uq for k in ALLOW)
        if sci_mode and is_writing:      # sci 模式只收「非寫作」領域
            continue
        if not sci_mode and not is_writing:
            continue
        label = uq.split("/")[-1].replace("壓縮檔", "").replace(".zip", "")[:22]
        try:
            res = extract_table(fetch(HOST + link.replace(" ", "%20")))
            if not res:
                files_skip += 1; print("SKIP", label, "(no table)"); continue
            kind, data = res
            rows = (rows_from_xlsx(data) if kind == "xlsx"
                    else rows_from_ods(data) if kind == "ods" else rows_from_docx(data))
        except Exception as e:
            files_skip += 1; print("FAIL", label, str(e)[:50]); continue

        hdr = None
        for ri in range(min(8, len(rows))):
            ti, zi = find_cols(rows[ri])
            if ti is not None and zi is not None:
                hdr, tw_i, zh_i = ri, ti, zi; break
        if hdr is None:
            files_skip += 1; print("SKIP", label, "(no 中文/大陸 欄)"); continue

        added = 0
        for row in rows[hdr + 1:]:
            if len(row) <= max(tw_i, zh_i):
                continue
            tw_list = split_cell(strip_annot(row[tw_i]))[:3]
            zh_raw = split_cell(strip_annot(row[zh_i]))
            if not tw_list or not zh_raw:
                continue
            for z in zh_raw:
                zh_w = s2t(z, M)          # 大陸簡體 → 繁體
                if (len(zh_w) < 2 or zh_w in DENY or zh_w in whitelist or zh_w in existing
                        or zh_w in tw_list or not any("一" <= c <= "鿿" for c in zh_w)):
                    continue
                d["grey"].append({"zh": zh_w, "tw": tw_list,
                                  "note": f"兩岸學術名詞-{label}(國教院)", "source": src_tag})
                existing.add(zh_w); added += 1
        total += added; files_ok += 1
        print(f"  {label}: +{added}")

    d.setdefault("_meta", {})["last_naer_domains"] = "2026-06-19 國教院 49 領域兩岸對照(s2t)"
    json.dump(d, open(DICT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nDOMAINS done: ok={files_ok} skip={files_skip}, +grey {total} "
          f"| TOTAL hard={len(d['hard'])} grey={len(d['grey'])} context={len(d['context'])}")


if __name__ == "__main__":
    main()
