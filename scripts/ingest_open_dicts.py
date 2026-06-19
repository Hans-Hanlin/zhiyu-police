# -*- coding: utf-8 -*-
"""把開源台灣詞庫 ingest 進 taiwanizer_dict.json（重品質、不過度誤抓）。

來源（授權乾淨才用）：
  - OpenCC TWPhrasesIT.txt      Apache-2.0   IT 詞 → 全進 hard
  - AKuKu StopChLang suggestions MIT          科技/食物/生活→hard、網路流行語→grey、政治/地域/國族→skip
原始檔存到 references/sources/ 備查。既有手工詞優先、去重；灰色路由與白名單保護。
報告寫 UTF-8 檔，console 只印 ASCII 數字（避 Windows GBK）。
"""
import urllib.request as u
import json, os, io, sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.join(os.path.dirname(__file__), "..")
DICT = os.path.join(BASE, "references", "taiwanizer_dict.json")
SRCDIR = os.path.join(BASE, "references", "sources")
os.makedirs(SRCDIR, exist_ok=True)

TW_IT = "https://raw.githubusercontent.com/yichen0831/opencc-python/master/opencc/dictionary/TWPhrasesIT.txt"
AKUKU = "https://raw.githubusercontent.com/AKuKu-Taiwan/StopChLang_Dictionary/master/dictionary.json"

# 灰色路由：這些就算來源標 hard，也降級成 grey（台灣已融入/語境敏感，避免硬改）
GREY_ROUTE = {
    "迭代", "優化", "數據", "用戶", "智能", "通過", "靠譜", "顏值", "內捲", "躺平",
    "變現", "痛點", "落地", "立馬", "水平", "渠道", "復盤", "對齊", "賦能", "抓手",
    "顆粒度", "閉環", "賽道", "高端", "高大上", "走心", "合規", "給力", "報錯",
    "視頻號", "社區",
}


def fetch(url):
    req = u.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return u.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def clean_alts(val, seps="／/、，,| "):
    import re
    parts = re.split("[" + "".join(seps) + "]+", val.strip())
    out = []
    for p in parts:
        p = p.strip()
        if p and p not in out:
            out.append(p)
    return out[:3] or [val.strip()]


def main():
    d = json.load(open(DICT, encoding="utf-8"))
    whitelist = set(d.get("whitelist", []))
    existing = ({e["zh"] for e in d["hard"]} | {e["zh"] for e in d["grey"]}
                | {e["zh"] for e in d.get("context", [])})   # context 假朋友不可被重收

    added_hard, added_grey, skipped = [], [], 0

    def consider(zh, tw_list, note, tier_hint):
        nonlocal skipped
        zh = zh.strip()
        if len(zh) < 2 or zh in whitelist or zh in existing:
            skipped += 1
            return
        if not tw_list or zh == tw_list[0]:   # 無台灣詞 / 自映射(zh==tw) 一律跳過
            skipped += 1
            return
        if not any("一" <= c <= "鿿" for c in zh):  # 非中文(英文縮寫如 YYDS)跳過
            skipped += 1
            return
        tier = "grey" if (zh in GREY_ROUTE or tier_hint == "grey") else "hard"
        entry = {"zh": zh, "tw": tw_list, "note": note, "source": note_src}
        (added_grey if tier == "grey" else added_hard).append(entry)
        existing.add(zh)

    # 1. OpenCC TWPhrasesIT → hard
    note_src = "opencc-IT"
    it_raw = fetch(TW_IT)
    open(os.path.join(SRCDIR, "TWPhrasesIT.txt"), "w", encoding="utf-8").write(it_raw)
    for line in it_raw.splitlines():
        if not line or line.startswith("#") or "\t" not in line:
            continue
        zh, val = line.split("\t", 1)
        consider(zh, clean_alts(val), "IT 術語(OpenCC)", "hard")

    # 2. AKuKu suggestions（依實際分類名分流）
    #    hard: 科技類/食物類   grey: 生活類/網路用語(量大或共用詞，交人校對)   skip: 政治/地域/國家
    note_src = "支語檢查器"
    ak_raw = fetch(AKUKU)
    open(os.path.join(SRCDIR, "akuku_dictionary.json"), "w", encoding="utf-8").write(ak_raw)
    ak = json.loads(ak_raw)
    cats = ak.get("categories", {})

    def words_of(name):
        v = cats.get(name, [])
        return set(v.keys() if isinstance(v, dict) else v)

    skip_words = words_of("政治類") | words_of("地域類") | words_of("國家類")
    grey_words = words_of("生活類") | words_of("網路用語")
    for zh, tw in ak.get("suggestions", {}).items():
        if zh in skip_words:
            skipped += 1
            continue
        hint = "grey" if zh in grey_words else "hard"
        consider(zh, clean_alts(str(tw)), "支語檢查器收錄", hint)

    # 3. 合併寫回
    d["hard"].extend(added_hard)
    d["grey"].extend(added_grey)
    d.setdefault("_meta", {})["last_ingest"] = "2026-06-18 OpenCC-IT + 支語檢查器"
    json.dump(d, open(DICT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 4. 報告
    rpt = io.StringIO()
    rpt.write(f"ingest 完成：新增 hard {len(added_hard)}、grey {len(added_grey)}、skip {skipped}\n")
    rpt.write(f"字典現況：hard {len(d['hard'])}、grey {len(d['grey'])}、whitelist {len(whitelist)}\n\n")
    rpt.write("=== 新增 hard 範例(前30) ===\n")
    for e in added_hard[:30]:
        rpt.write(f"  {e['zh']} → {e['tw'][0]}  [{e['source']}]\n")
    rpt.write("\n=== 新增 grey(全部) ===\n")
    for e in added_grey:
        rpt.write(f"  {e['zh']} → {' / '.join(e['tw'])}  [{e['source']}]\n")
    open(os.path.join(BASE, "_ingest_report.txt"), "w", encoding="utf-8").write(rpt.getvalue())
    print(f"DONE hard+{len(added_hard)} grey+{len(added_grey)} skip={skipped} "
          f"| total hard={len(d['hard'])} grey={len(d['grey'])}")


if __name__ == "__main__":
    main()
