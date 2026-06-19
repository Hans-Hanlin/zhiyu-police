# -*- coding: utf-8 -*-
"""支語警察 常駐巡邏 hook（掛 Stop 事件）。

AI 每次回完話觸發：讀旗標 → 若 on，掃描剛剛那則 assistant 回覆 → 發現硬錯就把
報案摘要印到 stderr 提醒。設計成「只提醒、不阻擋、不改寫對話」，且任何錯誤都安靜吞掉，
絕不弄壞使用者的工作流。旗標 off（或讀不到）時完全靜默、零開銷。
"""
import sys, os, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
FLAG = os.path.join(os.path.expanduser("~"), ".claude", "taiwanizer.flag")


def is_on():
    try:
        with open(FLAG, encoding="utf-8") as f:
            return f.read().strip().lower() == "on"
    except Exception:
        return False


def last_assistant_text(transcript_path):
    """從 Claude Code transcript（JSONL）取最後一則 assistant 文字。"""
    text = ""
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") != "assistant" and rec.get("role") != "assistant":
                    continue
                msg = rec.get("message", rec)
                content = msg.get("content", "")
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    parts = [b.get("text", "") for b in content
                             if isinstance(b, dict) and b.get("type") == "text"]
                    if parts:
                        text = "\n".join(parts)
    except Exception:
        return ""
    return text


def main():
    try:
        if not is_on():
            return  # 巡邏關閉 → 靜默
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        tpath = payload.get("transcript_path") or payload.get("transcriptPath")
        if not tpath:
            return
        text = last_assistant_text(tpath)
        if not text.strip():
            return
        from police import scan
        r = scan(text, level=1)   # 巡邏只報 hard(與模式無關)，固定 level=1 免空掃 5 萬條 grey
        if not r["hard"]:
            return  # 只在有硬錯時出聲，避免吵
        lines = [f"🚨 支語警察巡邏：剛那則回覆有 {r['hard_count']} 處支語硬錯"]
        for h in r["hard"][:8]:
            lines.append(f"  {h['zh']} → {h['tw'][0]}")
        if r["hard_count"] > 8:
            lines.append("  …（還有更多，叫『支語警察』看完整報告）")
        lines.append("（要改正＋灰色地帶校對，跟我說『叫支語警察來』）")
        sys.stderr.write("\n".join(lines) + "\n")
    except Exception:
        return  # 任何意外都不可弄壞主流程


if __name__ == "__main__":
    main()
