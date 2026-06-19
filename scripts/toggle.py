# -*- coding: utf-8 -*-
"""支語警察 常駐巡邏開關。

    python toggle.py on        開啟巡邏
    python toggle.py off       關閉巡邏
    python toggle.py status    查目前狀態（預設）

旗標存在 ~/.claude/taiwanizer.flag（跨平台用 expanduser，Windows 是 %USERPROFILE%）。
"""
import sys, os

sys.stdout.reconfigure(encoding="utf-8")
FLAG = os.path.join(os.path.expanduser("~"), ".claude", "taiwanizer.flag")


def read_state():
    try:
        with open(FLAG, encoding="utf-8") as f:
            return f.read().strip().lower()
    except FileNotFoundError:
        return "off"


def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "status").strip().lower()
    if cmd in ("on", "開", "開啟", "enable"):
        os.makedirs(os.path.dirname(FLAG), exist_ok=True)
        with open(FLAG, "w", encoding="utf-8") as f:
            f.write("on")
        print("🚨 支語警察：常駐巡邏已【開啟】。之後每次 AI 回話都會自動巡一遍。")
    elif cmd in ("off", "關", "關閉", "disable"):
        os.makedirs(os.path.dirname(FLAG), exist_ok=True)
        with open(FLAG, "w", encoding="utf-8") as f:
            f.write("off")
        print("😴 支語警察：常駐巡邏已【關閉】。需要時再叫我（支語警察 開）。")
    else:
        print(f"支語警察巡邏狀態：{'開啟' if read_state() == 'on' else '關閉'}")


if __name__ == "__main__":
    main()
