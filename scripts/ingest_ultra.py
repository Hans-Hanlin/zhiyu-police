# -*- coding: utf-8 -*-
"""ULTRA 多源 ingestion：把多個已驗證的開源台灣詞庫併進 taiwanizer_dict.json。

分級原則（保精準）：
  hard  = 人工驗證 / 程式專用的高信心來源（cn2tw4programmer、本檔內 AGENT_HARD 策展清單）
  grey  = 廣泛權威但需校對的大庫（g0v csld 同實異名、OpenCC TWPhrases、aronhack、AGENT_GREY）
  skip  = 政治/國名、同名異實假朋友(未抓)、單欄特有檔(未抓)、非中文、單字、白名單、已存在
GREY_ROUTE 會把任何「台灣已融入」的詞強制降級成 grey，避免硬改誤傷。
每筆帶 source 欄位可稽核。原始檔存 references/sources/。
"""
import urllib.request as u
import json, os, io, sys, csv

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.join(os.path.dirname(__file__), "..")
DICT = os.path.join(BASE, "references", "taiwanizer_dict.json")
SRCDIR = os.path.join(BASE, "references", "sources")
os.makedirs(SRCDIR, exist_ok=True)

GREY_ROUTE = {
    "迭代", "優化", "數據", "用戶", "智能", "通過", "靠譜", "顏值", "內捲", "躺平",
    "變現", "痛點", "落地", "立馬", "水平", "渠道", "復盤", "對齊", "賦能", "抓手",
    "顆粒度", "閉環", "賽道", "高端", "高大上", "走心", "合規", "給力", "報錯",
    "視頻號", "社區", "算力", "套殼", "對標", "構建", "提交", "拉取", "序列化",
    "實例化", "容器化", "部署", "緩衝", "推理", "微調", "量化", "蒸餾", "幻覺",
    "開箱即用", "提示詞工程", "對齊", "函數",
}

# Agent 策展的 AI/coding 圈支語（字典常漏）。hard=明確支語、grey=台灣也用/借詞
AGENT_HARD = [
    ("大模型", ["大型語言模型", "LLM"], "AI圈：台灣寫全名"),
    ("智能體", ["AI 代理", "代理人", "agent"], "AI圈：台灣用代理"),
    ("刷榜", ["灌榜", "衝榜"], "leaderboard 黑話"),
    ("平替", ["平價替代", "替代品"], "電商/AI圈簡稱"),
    ("降本增效", ["降低成本提升效率"], "中國企業四字黑話"),
    ("拉齊", ["對齊", "同步", "取得共識"], "職場黑話"),
    ("倉庫", ["儲存庫", "repo"], "Git：台灣用儲存庫"),
    ("鏡像", ["映像檔", "映像"], "Docker image"),
    ("聯調", ["整合測試", "串接測試"], "integration test"),
    ("灰度發布", ["漸進式發布", "金絲雀發布"], "canary release"),
    ("複用", ["重用", "再利用"], "reuse"),
    ("健壯性", ["穩健性", "強健性"], "robustness"),
    ("魯棒性", ["穩健性", "強健性"], "robust 音譯，台灣不用"),
    ("性能", ["效能"], "performance"),
    ("報文", ["封包", "訊息"], "packet/message"),
    ("套接字", ["通訊端", "socket"], "台灣用通訊端"),
    ("字節", ["位元組"], "byte"),
    ("兼容", ["相容"], "compatible"),
    ("遞歸", ["遞迴"], "recursion"),
    ("編程", ["程式設計"], "programming"),
    ("字段", ["欄位"], "field"),
    ("面向對象", ["物件導向"], "OOP"),
    ("驅動程序", ["驅動程式"], "driver"),
    ("構造函數", ["建構式", "建構函式"], "constructor"),
    ("需求評審", ["需求審查", "需求審閱"], "requirement review"),
    ("合入", ["合併", "merge"], "台灣用合併"),
]
AGENT_GREY = [
    ("算力", ["運算力", "運算能力"], "AI算力，台灣偏運算力"),
    ("套殼", ["套皮", "換殼"], "包裝現成模型"),
    ("對標", ["對齊標竿", "benchmark"], "職場詞"),
    ("構建", ["建構", "建置"], "build，台灣偏建置"),
    ("提交", ["提交", "commit"], "Git，台灣也用"),
    ("拉取", ["拉取", "pull"], "Git，台灣也用"),
    ("序列化", ["序列化", "serialize"], "兩岸常見同字"),
    ("實例化", ["實體化", "建立執行個體"], "instantiate"),
    ("開箱即用", ["拿來就能用"], "out-of-the-box 中國譯法"),
    ("提示詞工程", ["提示工程"], "prompt engineering"),
    ("推理", ["推論"], "inference，台灣學界偏推論"),
]

SRC = {
    "csld_同實異名": "https://raw.githubusercontent.com/g0v/moedict-data-csld/master/%E5%85%A9%E5%B2%B8%E5%90%8C%E5%AF%A6%E7%95%B0%E5%90%8D.csv",
    "csld_三地": "https://raw.githubusercontent.com/g0v/moedict-data-csld/master/%E5%85%A9%E5%B2%B8%E4%B8%89%E5%9C%B0%E7%94%9F%E6%B4%BB%E5%B7%AE%E7%95%B0%E8%A9%9E%E8%AA%9E%E5%BD%99%E7%B7%A8-%E5%90%8C%E5%AF%A6%E7%95%B0%E5%90%8D.csv",
    "aronhack": "https://raw.githubusercontent.com/aronhack/Chinese-Vocabulary-Radar/main/chrome-extension/taiwan_china_vocabs.json",
    "cn2tw_prog": "https://raw.githubusercontent.com/PJCHENder/cn2tw4programmer/master/src/terms/_newTongWenTang.json",
    "opencc_TWPhrases": "https://raw.githubusercontent.com/BYVoid/OpenCC/master/data/dictionary/TWPhrases.txt",
}


def fetch(url):
    return u.urlopen(u.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read().decode("utf-8", "replace")


def main():
    d = json.load(open(DICT, encoding="utf-8"))
    whitelist = set(d.get("whitelist", []))
    existing = ({e["zh"] for e in d["hard"]} | {e["zh"] for e in d["grey"]}
                | {e["zh"] for e in d.get("context", [])})   # context 假朋友不可被重收
    stats = {"hard": 0, "grey": 0, "skip": 0}

    def consider(zh, tw, note, src, hint):
        zh = (zh or "").strip()
        tw = [t.strip() for t in tw if t and t.strip()][:3]
        if len(zh) < 2 or not tw or zh in whitelist or zh in existing:
            stats["skip"] += 1
            return
        if not any("一" <= c <= "鿿" for c in zh):
            stats["skip"] += 1
            return
        if zh == tw[0]:
            stats["skip"] += 1
            return
        tier = "grey" if (zh in GREY_ROUTE or hint == "grey") else "hard"
        d[tier].append({"zh": zh, "tw": tw, "note": note, "source": src})
        existing.add(zh)
        stats[tier] += 1

    # --- HARD: 策展 AI/coding ---
    for zh, tw, note in AGENT_HARD:
        consider(zh, tw, note, "策展-AIcoding", "hard")
    for zh, tw, note in AGENT_GREY:
        consider(zh, tw, note, "策展-AIcoding", "grey")

    # --- HARD: cn2tw4programmer (ISC) flat {陸:台} ---
    try:
        raw = fetch(SRC["cn2tw_prog"])
        open(os.path.join(SRCDIR, "cn2tw4programmer.json"), "w", encoding="utf-8").write(raw)
        for zh, tw in json.loads(raw).items():
            consider(zh, [str(tw)], "程式術語(cn2tw4programmer)", "cn2tw", "hard")
    except Exception as e:
        print("cn2tw FAIL", str(e)[:80])

    # --- GREY: OpenCC TWPhrases (Apache) 陸\t台 alts ---
    try:
        raw = fetch(SRC["opencc_TWPhrases"])
        open(os.path.join(SRCDIR, "TWPhrases.txt"), "w", encoding="utf-8").write(raw)
        for line in raw.splitlines():
            if not line or line.startswith("#") or "\t" not in line:
                continue
            zh, val = line.split("\t", 1)
            consider(zh, val.split(), "OpenCC 台灣慣用詞", "opencc-TW", "grey")
    except Exception as e:
        print("opencc FAIL", str(e)[:80])

    # --- GREY: aronhack (CC0) [{chinese, taiwanese}] ---
    try:
        raw = fetch(SRC["aronhack"])
        open(os.path.join(SRCDIR, "aronhack.json"), "w", encoding="utf-8").write(raw)
        for o in json.loads(raw):
            consider(o.get("chinese", ""), [o.get("taiwanese", "")], "aronhack 收錄", "aronhack", "grey")
    except Exception as e:
        print("aronhack FAIL", str(e)[:80])

    # --- GREY: g0v csld 同實異名 (CC BY-NC-ND, 自用) col0=台 col3=陸 ---
    try:
        raw = fetch(SRC["csld_同實異名"])
        open(os.path.join(SRCDIR, "csld_同實異名.csv"), "w", encoding="utf-8").write(raw)
        for i, row in enumerate(csv.reader(io.StringIO(raw))):
            if i == 0 or len(row) < 4:      # 跳過標題列
                continue
            tw_w, zh_w = row[0].strip(), row[3].strip()
            if tw_w and zh_w and zh_w not in ("大陸詞", "陸詞"):
                consider(zh_w, [tw_w], "兩岸同實異名(g0v csld)", "csld", "grey")
    except Exception as e:
        print("csld FAIL", str(e)[:80])

    # --- GREY: g0v csld 三地 同實異名  col4=臺1 col7=陸1 ---
    try:
        raw = fetch(SRC["csld_三地"])
        open(os.path.join(SRCDIR, "csld_三地_同實異名.csv"), "w", encoding="utf-8").write(raw)
        rd = list(csv.reader(io.StringIO(raw)))
        for row in rd[1:]:
            if len(row) < 8:
                continue
            tw_w, zh_w = row[4].strip(), row[7].strip()
            if tw_w and zh_w:
                consider(zh_w, [tw_w], "兩岸三地同實異名(g0v csld)", "csld3", "grey")
    except Exception as e:
        print("csld3 FAIL", str(e)[:80])

    d.setdefault("_meta", {})["last_ultra_ingest"] = "2026-06-19 cn2tw+OpenCC-TW+aronhack+g0v-csld+策展AIcoding"
    json.dump(d, open(DICT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"ULTRA done: +hard {stats['hard']}, +grey {stats['grey']}, skip {stats['skip']} "
          f"| TOTAL hard={len(d['hard'])} grey={len(d['grey'])} whitelist={len(whitelist)}")


if __name__ == "__main__":
    main()
