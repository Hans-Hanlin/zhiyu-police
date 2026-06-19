# -*- coding: utf-8 -*-
"""支語警察偵測引擎（字典比對層）。

用法：
    python police.py <檔案路徑>        # 掃描檔案
    echo "文字" | python police.py     # 從 stdin 掃描
    python police.py --json <檔案>     # 只輸出 JSON（給 hook / 程式用）

輸出：硬錯(hard) + 灰色地帶(grey) + 簡體字(simplified) + 自動改正後的文字(corrected_text)。
硬錯直接給出改正；灰色地帶只標記、不自動改，交由人或 LLM 判斷語境。
本層只做確定性字典比對；語境型支語（句式、組合詞）由 SKILL 指示 LLM 補抓。
"""
import sys, json, io, os

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_REF = os.path.join(os.path.dirname(__file__), "..", "references")
# 本機完整詞庫（含 csld/NAER 等授權受限、不公開散布的擴充）優先；公開 clone 用乾淨子集
DICT_LOCAL = os.path.join(_REF, "taiwanizer_dict.full.local.json")
DICT_PATH = DICT_LOCAL if os.path.exists(DICT_LOCAL) else os.path.join(_REF, "taiwanizer_dict.json")

# ─── 分級制 ─────────────────────────────────────────────────────
# 普通版(1)=日常/AI/tech 高頻；進階版(2)=+NAER 寫作領域；檢察官 ULTRA(3)=+冷僻科學
# 未列出的 source（curated / opencc-* / 支語檢查器 / cn2tw / aronhack / 策展-AIcoding /
# curated-name / reviewed / naer 一般名詞…）一律屬普通版(1)。
LEVEL_BY_SOURCE = {"naer-dom": 2, "naer-sci": 3}
LEVEL_NAME = {1: "普通版", 2: "進階版", 3: "支語檢察官 ULTRA"}
FLAG_LEVEL = os.path.join(os.path.expanduser("~"), ".claude", "taiwanizer.level")


def active_level():
    """讀目前模式（1/2/3）；預設普通版(1)。"""
    try:
        n = int(open(FLAG_LEVEL, encoding="utf-8").read().strip())
        return n if n in (1, 2, 3) else 1
    except Exception:
        return 1

# 純簡體字（繁簡共用字如 量/默/硬/据 不可放進來，否則誤判繁體文——
# 例『据』在『拮据』是合法繁體）。出現代表簡轉繁沒做乾淨。
SIMPLIFIED = set("软视频质数网络链认调试变针队优级别这来们时实个码扩压标节")


def load_dict():
    with open(DICT_PATH, encoding="utf-8") as f:
        return json.load(f)


def protected_ranges(text, whitelist):
    """回傳白名單詞在文中佔據的字元範圍，避免誤抓白名單詞的子字串。"""
    spans = []
    for w in whitelist:
        start = 0
        while True:
            i = text.find(w, start)
            if i < 0:
                break
            spans.append((i, i + len(w)))
            start = i + 1
    return spans


def in_protected(pos, length, spans):
    s, e = pos, pos + length
    return any(ps <= s and e <= pe for ps, pe in spans)


def find_hits(text, entries, spans):
    """回傳命中清單；每筆含實際非保護位置 positions（供精準改正用）。"""
    hits = []
    for ent in entries:
        zh = ent["zh"]
        positions, start = [], 0
        while True:
            i = text.find(zh, start)
            if i < 0:
                break
            if not in_protected(i, len(zh), spans):
                positions.append(i)
            start = i + 1
        if positions:
            hits.append({"zh": zh, "tw": ent.get("tw", [zh]), "note": ent.get("note", ""),
                         "count": len(positions), "positions": positions})
    return hits


def correct_hard(text, hard_hits):
    """以「位置式、不重疊、長詞優先」精準改正硬錯。

    只動 find_hits 已算出的非保護位置（白名單詞內不碰）；長詞先佔位、與已佔位重疊的短詞
    跳過——一次根治三個問題：白名單污染、級聯替換(演算法→演演算法)、子字串重複(互聯網→互聯)。
    """
    cand = []  # (pos, len, repl)
    for h in hard_hits:
        tw = h.get("tw") or []
        repl = tw[0] if tw else h["zh"]
        if repl == h["zh"]:
            continue  # 自映射（zh==tw）不改，避免無謂變動
        L = len(h["zh"])
        for pos in h.get("positions", []):
            cand.append((pos, L, repl))
    # 長詞優先佔位；與已接受區間重疊者跳過
    cand.sort(key=lambda s: (-s[1], s[0]))
    accepted, occupied = [], []
    for pos, L, repl in cand:
        s, e = pos, pos + L
        if any(not (e <= os or s >= oe) for os, oe in occupied):
            continue
        occupied.append((s, e))
        accepted.append((s, e, repl))
    # 依位置重組字串
    accepted.sort(key=lambda a: a[0])
    out, cur = [], 0
    for s, e, repl in accepted:
        if s < cur:
            continue
        out.append(text[cur:s])
        out.append(repl)
        cur = e
    out.append(text[cur:])
    return "".join(out)


def scan(text, level=None):
    if level not in (1, 2, 3):      # 非法/None 一律回退到旗標或預設普通版
        level = active_level()
    d = load_dict()
    spans = protected_ranges(text, d.get("whitelist", []))
    hard = find_hits(text, d.get("hard", []), spans)
    # grey 依模式分層：只取 level <= 目前模式的條目
    grey_pool = [e for e in d.get("grey", []) if LEVEL_BY_SOURCE.get(e.get("source"), 1) <= level]
    grey = find_hits(text, grey_pool, spans)
    context = find_hits(text, d.get("context", []), spans)   # 同名異實：絕不自動改
    simp = sorted({c for c in text if c in SIMPLIFIED})
    corrected = correct_hard(text, hard) if hard else text     # context 不進 corrected
    return {
        "hard": hard,
        "grey": grey,
        "context": context,
        "simplified": simp,
        "hard_count": sum(h["count"] for h in hard),
        "grey_count": sum(g["count"] for g in grey),
        "context_count": sum(c["count"] for c in context),
        "corrected_text": corrected,
        "level": level,
    }


def main():
    argv = sys.argv[1:]
    json_only = "--json" in argv
    level = None
    consumed = set()        # 被 --level 吃掉的 index
    if "--level" in argv:
        i = argv.index("--level")
        consumed.add(i)
        # 只有當下一個 token 是純數字才把它當等級值消耗
        if i + 1 < len(argv) and argv[i + 1].lstrip("-").isdigit():
            level = int(argv[i + 1])
            consumed.add(i + 1)
    args = [a for i, a in enumerate(argv) if a != "--json" and i not in consumed]
    if len(args) > 1:
        sys.stderr.write(f"[police] 一次只掃一個檔，忽略其餘：{args[1:]}\n")
    if args:
        with open(args[0], encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    result = scan(text, level=level)

    if json_only:
        print(json.dumps(result, ensure_ascii=False))
        return

    # 人類可讀摘要
    mode = LEVEL_NAME.get(result.get("level", 1), "普通版")
    if (not result["hard"] and not result["grey"]
            and not result.get("context") and not result["simplified"]):
        print(f"✅ 支語警察（{mode}）：本篇沒抓到支語，乾淨。")
        return
    print(f"🚨 支語警察報案紀錄（{mode}）：硬錯 {result['hard_count']} 處、灰色地帶 "
          f"{result['grey_count']} 處、同名異實 {result.get('context_count', 0)} 處")
    if result["simplified"]:
        print(f"⚠️ 夾帶簡體字：{' '.join(result['simplified'])}")
    if result["hard"]:
        print("\n【硬錯 — 已直接改正】")
        for h in result["hard"]:
            print(f"  {h['zh']} → {h['tw'][0]}　({h['note']})　×{h['count']}")
    if result["grey"]:
        print("\n【灰色地帶 — 請你校對是否要改】")
        for g in result["grey"]:
            alts = " / ".join(g["tw"])
            print(f"  {g['zh']} → {alts}　({g['note']})　×{g['count']}")
    if result.get("context"):
        print("\n【⚠️ 同名異實 — 看你是哪個意思，絕不自動改】")
        for c in result["context"]:
            print(f"  {c['zh']}：{c['note']}　×{c['count']}")


if __name__ == "__main__":
    main()
