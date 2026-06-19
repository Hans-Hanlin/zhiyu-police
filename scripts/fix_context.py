# -*- coding: utf-8 -*-
"""把『同名異實假朋友』從 hard/grey 抽出，獨立成 context 級（看語境、絕不自動改）。
這類詞在台灣有合法意思，硬改會改錯（例：台灣『土豆』=花生，改成馬鈴薯就錯了）。"""
import json, os

DICT = os.path.join(os.path.dirname(__file__), "..", "references", "taiwanizer_dict.json")

# 同名異實：台灣與中國同字不同義。tw=「若你指支語那個意思」的台灣詞；note 講清楚兩義。
CONTEXT = [
    {"zh": "土豆",
     "tw": ["馬鈴薯"],
     "note": "台灣『土豆』通常指【花生】(源自台語，講習慣了)；中國『土豆』指【馬鈴薯】。"
             "你要說馬鈴薯就直接寫『馬鈴薯』(台灣只有這個講法)；要說花生，『土豆/花生』都對、別改。"},
    {"zh": "質量",
     "tw": ["品質"],
     "note": "台灣『質量』=物理的 mass(質量守恆)；表 quality 要用『品質』。"
             "若你指品質→改『品質』；若真在講物理質量→維持別改。"},
    {"zh": "水平",
     "tw": ["水準"],
     "note": "台灣『水平』=horizontal(水平線/水平方向)；表『程度高低』要用『水準』。看你哪個意思。"},
]
CONTEXT_ZH = {e["zh"] for e in CONTEXT}

d = json.load(open(DICT, encoding="utf-8"))

def strip(lst):
    return [e for e in lst if e["zh"] not in CONTEXT_ZH]

before = (len(d["hard"]), len(d.get("grey", [])))
d["hard"] = strip(d["hard"])
d["grey"] = strip(d["grey"])

# 土豆條：台灣不講(炸的叫薯條)，但跟土豆同源、易混 → 降到 grey 不硬改
for e in list(d["hard"]):
    if e["zh"] == "土豆條":
        d["hard"].remove(e)
        e["note"] = "中國『土豆條』=薯條；台灣講薯條。注意『土豆』在台灣是花生，勿混"
        d["grey"].append(e)

d["context"] = CONTEXT
json.dump(d, open(DICT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"hard {before[0]}->{len(d['hard'])}, grey {before[1]}->{len(d['grey'])}, "
      f"context={len(d['context'])} ({','.join(CONTEXT_ZH)})")
