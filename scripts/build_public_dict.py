# -*- coding: utf-8 -*-
"""產生可開源散布的乾淨詞庫 references/taiwanizer_dict.json。

只保留授權允許公開再散布的來源（Apache-2.0 / MIT / ISC / CC0 / 本專案自有）；
排除 CC BY-NC-ND 的 g0v csld 與授權未確認的 NAER 政府資料——這兩類由使用者自行跑
`ingest_*.py` 在本機補充（並自負授權責任）。

讀全量本機詞庫 taiwanizer_dict.full.local.json（若無則讀現有 taiwanizer_dict.json），
輸出公開子集到 taiwanizer_dict.json（給 repo commit）。
"""
import json, os, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
REF = os.path.join(os.path.dirname(__file__), "..", "references")
FULL = os.path.join(REF, "taiwanizer_dict.full.local.json")
PUB = os.path.join(REF, "taiwanizer_dict.json")

# 可公開再散布的來源
ALLOWED = {None, "", "curated", "reviewed", "策展-AIcoding", "curated-name",
           "cn2tw", "opencc-IT", "opencc-TW", "支語檢查器", "aronhack"}
# 排除（授權受限，使用者本機自取）
EXCLUDED_NOTE = {
    "csld / csld3": "g0v 萌典兩岸詞典 — CC BY-NC-ND 4.0（禁改作/商用，不可公開散布衍生）",
    "naer / naer-dom / naer-sci": "國教院樂詞網 — 政府資料授權未逐項確認，保守不散布",
}


def keep(e):
    return e.get("source") in ALLOWED


def main():
    src = FULL if os.path.exists(FULL) else PUB
    d = json.load(open(src, encoding="utf-8"))
    pub = {
        "_meta": {
            "desc": "支語警察公開詞庫（僅含可再散布來源）。完整學術/csld 擴充請本機跑 ingest_*.py。",
            "license_note": EXCLUDED_NOTE,
            "version": "public-2026-06-19",
        },
        "hard": [e for e in d.get("hard", []) if keep(e)],
        "grey": [e for e in d.get("grey", []) if keep(e)],
        "context": d.get("context", []),       # 全為自有/reviewed
        "whitelist": d.get("whitelist", []),
    }
    json.dump(pub, open(PUB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"公開詞庫產生：hard {len(pub['hard'])} grey {len(pub['grey'])} "
          f"context {len(pub['context'])} whitelist {len(pub['whitelist'])} "
          f"= {sum(len(pub[k]) for k in ('hard','grey','context','whitelist'))}")
    excl = Counter(e.get("source") for e in d.get("hard", []) + d.get("grey", []) if not keep(e))
    print("排除（授權受限，使用者自取）：", dict(excl))


if __name__ == "__main__":
    main()
