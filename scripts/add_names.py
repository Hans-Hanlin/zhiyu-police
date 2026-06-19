# -*- coding: utf-8 -*-
"""加精選「兩岸人名/地名/品牌譯名」差異（高頻可靠，放普通版 L1 grey）。
NAER 66k 譯名是英→台單向、無法成對，故改用精選常見差異。順手擋掉 L3 漏進的超常見詞。"""
import json, os
DICT = os.path.join(os.path.dirname(__file__), "..", "references", "taiwanizer_dict.json")

NAMES = [
    # 國名 / 地名
    ("新西蘭", ["紐西蘭"]), ("老撾", ["寮國"]), ("悉尼", ["雪梨"]), ("戛納", ["坎城"]),
    ("硅谷", ["矽谷"]), ("卡塔爾", ["卡達"]), ("沙特", ["沙烏地阿拉伯"]), ("也門", ["葉門"]),
    ("危地馬拉", ["瓜地馬拉"]), ("厄瓜多爾", ["厄瓜多"]), ("埃塞俄比亞", ["衣索比亞"]),
    ("津巴布韋", ["辛巴威"]), ("莫桑比克", ["莫三比克"]), ("博茨瓦納", ["波札那"]),
    ("尼日利亞", ["奈及利亞"]), ("科特迪瓦", ["象牙海岸"]), ("毛里求斯", ["模里西斯"]),
    ("阿塞拜疆", ["亞塞拜然"]), ("格魯吉亞", ["喬治亞"]), ("塞拉利昂", ["獅子山"]),
    ("馬爾代夫", ["馬爾地夫"]), ("柬埔寨", ["柬埔寨"]), ("文萊", ["汶萊"]),
    ("朝鮮", ["北韓"]), ("first", ["首爾"]),  # placeholder removed below
    # 人名
    ("奧巴馬", ["歐巴馬"]), ("特朗普", ["川普"]), ("普京", ["普丁"]), ("布什", ["布希"]),
    ("戈爾巴喬夫", ["戈巴契夫"]), ("喬布斯", ["賈伯斯"]), ("比爾蓋茨", ["比爾蓋茲"]),
    ("貝克漢姆", ["貝克漢"]), ("梅西", ["梅西"]), ("克林頓", ["柯林頓"]),
    ("奧巴梅揚", ["奧巴梅揚"]), ("馬拉多納", ["馬拉度納"]), ("貝多芬", ["貝多芬"]),
    # 品牌
    ("奔馳", ["賓士"]), ("大眾汽車", ["福斯汽車"]), ("雷克薩斯", ["凌志"]),
    ("惠普", ["惠普", "HP"]), ("強生", ["嬌生"]), ("歐萊雅", ["萊雅"]),
]

d = json.load(open(DICT, encoding="utf-8"))
whitelist = set(d.get("whitelist", []))
existing = {e["zh"] for e in d["hard"]} | {e["zh"] for e in d["grey"]} | {e["zh"] for e in d.get("context", [])}

# 擋掉 L3 漏進的超常見共用詞（whitelist 保護所有模式）
for w in ["應用", "使用", "方法", "系統", "過程", "功能", "資訊", "服務"]:
    if w not in whitelist:
        d["whitelist"].append(w); whitelist.add(w)

added = 0
for zh, tw in NAMES:
    if zh in ("first",) or zh == tw[0] or zh in whitelist or zh in existing or len(zh) < 2:
        continue
    d["grey"].append({"zh": zh, "tw": tw, "note": "兩岸人名/地名/品牌譯名", "source": "curated-name"})
    existing.add(zh); added += 1

json.dump(d, open(DICT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"人名地名 +{added}（grey L1）, whitelist={len(d['whitelist'])}, "
      f"hard={len(d['hard'])} grey={len(d['grey'])}")
