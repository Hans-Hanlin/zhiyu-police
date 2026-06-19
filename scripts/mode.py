# -*- coding: utf-8 -*-
"""支語警察模式切換：普通版(1) / 進階版(2) / 支語檢察官 ULTRA(3)。

    python mode.py 普通      切普通版（常態、~2.6k 條、快、零誤判）
    python mode.py 進階      切進階版（~7k、含 NAER 寫作領域）
    python mode.py 檢察官    切 ULTRA（全部 ~5萬+、含冷僻科學/人名地名，深度法辦用）
    python mode.py status    查目前模式（預設）
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
FLAG = os.path.join(os.path.expanduser("~"), ".claude", "taiwanizer.level")
NAME = {1: "普通版（~2.6k）", 2: "進階版（~7k）", 3: "支語檢察官 ULTRA（~5萬+）"}

ALIASES = {
    "普通": 1, "普通版": 1, "normal": 1, "1": 1, "基本": 1,
    "進階": 2, "進階版": 2, "advanced": 2, "2": 2,
    "檢察官": 3, "支語檢察官": 3, "檢查官": 3, "ultra": 3, "ULTRA": 3, "3": 3, "法辦": 3,
}


def current():
    try:
        n = int(open(FLAG, encoding="utf-8").read().strip())
        return n if n in NAME else 1
    except Exception:
        return 1


def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "status").strip()
    if cmd in ("status", "狀態", ""):
        print(f"支語警察目前模式：{NAME[current()]}")
        return
    lv = ALIASES.get(cmd.lower()) or ALIASES.get(cmd)
    if not lv:
        print(f"未知模式「{cmd}」。可用：普通 / 進階 / 檢察官")
        return
    os.makedirs(os.path.dirname(FLAG), exist_ok=True)
    open(FLAG, "w", encoding="utf-8").write(str(lv))
    print(f"🚨 支語警察已切換到【{NAME[lv]}】"
          + ("　逐字法辦模式啟動，連冷僻科學詞都抓。" if lv == 3 else ""))


if __name__ == "__main__":
    main()
