# -*- coding: utf-8 -*-
"""支語警察「人工核對回饋閉環」——把你審完的判斷寫回詞庫，越用越強。

支語檢察官(ULTRA)深審後一定有些要人工判斷的；你給判斷，用這個寫回，詞庫就進化：

    python learn.py whitelist 互聯 聯網      # 誤判/不該抓 → 加白名單(所有模式都不再抓)
    python learn.py promote 算力             # 確認是明確支語 → 升級成 hard(自動改、進普通版)
    python learn.py demote 視頻              # 太武斷 → 從 hard 降到 grey(只提示)
    python learn.py context 土豆 "台=花生/陸=馬鈴薯，看語境"   # 標成同名異實，絕不自動改
    python learn.py fix 轉發 轉貼,分享        # 配對錯 → 改台灣詞
    python learn.py drop 轉發                # 整條刪掉(根本不是支語/壞配對)

每次操作都記到 references/_review_log.jsonl，可追溯。
"""
import json, os, sys, io
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.join(os.path.dirname(__file__), "..")
DICT = os.path.join(BASE, "references", "taiwanizer_dict.json")
LOG = os.path.join(BASE, "references", "_review_log.jsonl")


def load():
    return json.load(open(DICT, encoding="utf-8"))


def save(d):
    # 原子寫入：先寫暫存檔再 os.replace，避免中斷時截斷這份唯一真相詞庫
    for k in ("hard", "grey", "context", "whitelist"):
        d.setdefault(k, [])
    tmp = DICT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, DICT)


def log(action, detail):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    except Exception:
        ts = "?"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts, "action": action, **detail}, ensure_ascii=False) + "\n")


def remove_from(d, zh, tiers=("hard", "grey", "context")):
    moved = None
    for t in tiers:
        for e in list(d.get(t, [])):
            if e["zh"] == zh:
                d[t].remove(e); moved = e
    return moved


def main():
    if len(sys.argv) < 3:
        print(__doc__); return
    action, words = sys.argv[1], sys.argv[2:]
    d = load()

    d.setdefault("whitelist", [])
    for k in ("hard", "grey", "context"):
        d.setdefault(k, [])

    if action == "whitelist":
        for zh in words:
            remove_from(d, zh)
            if zh not in d["whitelist"]:
                d["whitelist"].append(zh)
        log("whitelist", {"words": words})
        print(f"✅ 已加白名單(不再抓)：{' '.join(words)}")

    elif action == "unwhitelist":      # 移除誤加的白名單詞
        for zh in words:
            if zh in d["whitelist"]:
                d["whitelist"].remove(zh)
        log("unwhitelist", {"words": words})
        print(f"✅ 已移出白名單：{' '.join(words)}")

    elif action == "promote":
        for zh in words:
            e = remove_from(d, zh)      # 全層移除，避免 hard 產生重複
            tw = e["tw"] if (e and e.get("tw")) else None
            if not tw:
                print(f"⚠️ {zh} 詞庫沒有對應台灣詞，請先用 fix 指定：learn.py fix {zh} <台灣詞>")
                continue
            d["hard"].append({"zh": zh, "tw": tw,
                              "note": (e or {}).get("note", "人工確認支語"), "source": "reviewed"})
        log("promote", {"words": words})
        print(f"✅ 升級為硬錯(自動改、進普通版)：{' '.join(words)}")

    elif action == "demote":
        for zh in words:
            e = remove_from(d, zh, ("hard",))
            if e:
                e["source"] = "reviewed"; d["grey"].append(e)
        log("demote", {"words": words})
        print(f"✅ 降為灰色(只提示)：{' '.join(words)}")

    elif action == "context":
        zh = words[0]
        note = words[1] if len(words) > 1 else "同名異實，看語境"
        old = remove_from(d, zh)
        tw = old["tw"] if old else [zh]
        d.setdefault("context", []).append({"zh": zh, "tw": tw, "note": note, "source": "reviewed"})
        log("context", {"zh": zh, "note": note})
        print(f"✅ 標為同名異實(絕不自動改)：{zh}")

    elif action == "fix":
        if len(words) < 2:
            print("用法：learn.py fix <詞> <台灣詞[,詞2]>"); return
        zh, tw = words[0], [t.strip() for t in words[1].split(",") if t.strip()]
        if not tw:
            print("台灣詞不可為空"); return
        hit = False
        for t in ("hard", "grey", "context"):
            for e in d.get(t, []):
                if e["zh"] == zh:
                    e["tw"] = tw; e["source"] = "reviewed"; hit = True
        log("fix", {"zh": zh, "tw": tw})
        print(f"{'✅ 已修正配對' if hit else '⚠️ 詞庫沒這條'}：{zh} → {' / '.join(tw)}")

    elif action == "drop":
        for zh in words:
            remove_from(d, zh)
        log("drop", {"words": words})
        print(f"✅ 已刪除：{' '.join(words)}")

    else:
        print(__doc__); return

    save(d)
    print(f"   詞庫現況 hard={len(d['hard'])} grey={len(d['grey'])} "
          f"context={len(d.get('context', []))} whitelist={len(d['whitelist'])}")


if __name__ == "__main__":
    main()
