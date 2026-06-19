<div align="center">

# 🚨 支語警察

### 把中文台灣化 — 揪出混進來的支語，改回台灣慣用語
**taiwanizer** · Detect Mainland-Chinese vocabulary in your writing and convert it back to **Taiwanese Mandarin**

[![License: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)
![Taiwan](https://img.shields.io/badge/lang-繁體中文%20·%20Taiwan-blue)
![Model-agnostic](https://img.shields.io/badge/works%20with-any%20AI%20agent-orange)

</div>

---

用 AI 寫完稿後特別好用 —— LLM 的中文語料以簡體 / 中國來源為主，常產出「**繁體皮、簡體骨**」的文字
（視頻、質量、默認、調用、數據庫…），這層**詞彙**偏移連簡繁轉換工具都修不掉，正是本工具要補的洞。
語言是台灣大家的文化財；這工具不是嘴砲糾察，而是**正經的糾錯與改正**，幫你的中文保有台灣語感。

> Because most LLM Chinese training data is Simplified/Mainland-sourced, even "Traditional Chinese" output is
> often *Traditional glyphs with Mainland word choices*. Char-level 簡→繁 converters can't fix this — it's a
> **word-level** problem. 支語警察 fixes it.

---

## 🤖 不限 Claude，任何模型 / Agent 都能用 · Model-agnostic

核心是**純 Python**（詞庫比對 + 改正），完全不綁定特定模型：

- **獨立執行 standalone**：`python scripts/police.py 你的稿.txt` —— 不需要任何 AI。
- **接任何 AI Agent**：Claude Code、OpenAI Codex、Cursor、Gemini CLI… 凡是支援 skill / tool / 自訂指令的，
  都能把它當一個技能掛上去（本 repo 附 `SKILL.md` 為 Claude Code/Codex 通用 skill 格式）。
- **接你自己的程式**：`--json` 輸出結構化結果，串進任何 pipeline。

## ✨ 特色 · Features

- **四級判定，不矯枉過正** (4-tier judgment, no over-correction)
  - 🔴 **硬錯 hard**：台灣基本不用的支語，直接改正（軟件→軟體、視頻→影片、默認→預設）
  - 🟡 **灰色地帶 grey**：台灣也用 / 已融入，只列出來請你校對、不強制（迭代、優化、數據）
  - ⚠️ **同名異實 false-friend**：兩岸同字不同義，絕不自動改、只提示（**土豆**：台=花生 / 陸=馬鈴薯）
  - ⚪ **白名單 whitelist**：看似支語其實台灣本來就用，絕不誤抓（社群、渲染、部署、資訊）
- **三級偵測強度**：普通版 / 進階版 / 支語檢察官 ULTRA — 平常精準、發文前可深度法辦
- **人工核對回饋閉環**：審完的判斷一行寫回詞庫，越用越強 (a feedback loop that grows the dictionary)

## 🚀 用法 · Usage

```bash
python scripts/police.py 你的稿.txt              # 掃描 + 改正
python scripts/police.py 你的稿.txt --level 3     # 單次最高階（支語檢察官 ULTRA）
python scripts/police.py 你的稿.txt --json        # 結構化輸出，串接程式
python scripts/mode.py 普通                       # 切模式：普通 / 進階 / 檢察官 / status
```

在 AI Agent 對話裡（Claude Code / Codex / Cursor / Gemini CLI…）直接說：
> 「**叫支語警察來**」「這篇有沒有支語」「用支語檢察官審一下」

### 三級模式 · Three modes

| 模式 Mode | 內容 | 何時用 |
|------|------|--------|
| **普通版 Normal**（預設）| 日常/AI/coding 高頻 + 精選人名地名 + 同名異實 | 平常寫稿、快、零誤判 |
| **進階版 Advanced** | + 寫作相關學術領域 | 寫長文、要更嚴 |
| **支語檢察官 ULTRA** | + 冷僻科學 jargon | 發文前逐字法辦（噪音較多、需人工複核）|

### 人工核對回饋閉環 · Feedback loop

```bash
python scripts/learn.py whitelist <詞>      # 誤判 → 不再抓
python scripts/learn.py promote <詞>        # 確認支語 → 升級硬錯
python scripts/learn.py context <詞> "說明" # 同名異實 → 看語境不自動改
python scripts/learn.py fix <詞> <台灣詞>   # 修配對
python scripts/learn.py drop <詞>           # 刪壞配對
```

## 📚 詞庫與授權 · Dictionary & licensing

本 repo 內建 `references/taiwanizer_dict.json` 是**可公開再散布的乾淨核心**（約 1,500 條），來源皆寬鬆授權：

| 來源 Source | 授權 License |
|------|------|
| OpenCC (TWPhrases / TWPhrasesIT) | Apache-2.0 |
| AKuKu StopChLang_Dictionary | MIT |
| pjchender/cn2tw4programmer | ISC |
| aronhack/Chinese-Vocabulary-Radar | CC0 |
| 本專案自有策展 / 人名地名 / 案例 | MIT (this repo) |

詳見 [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)。

**想要更大的詞庫（學術領域 / 兩岸詞典）**：g0v 萌典兩岸詞典（CC BY-NC-ND）與國教院樂詞網（政府資料）
因授權限制**不隨本 repo 散布**，可在本機自行執行匯入腳本擴充（並自負授權責任）：

```bash
python scripts/ingest_ultra.py          # OpenCC / cn2tw / aronhack / g0v csld
python scripts/ingest_naer.py           # 國教院 兩岸一般名詞
python scripts/ingest_naer_domains.py   # 國教院 寫作相關領域（--sci 收冷僻科學）
```

擴充後產生本機完整詞庫，`police.py` 會自動優先使用它。

## 📄 授權 · License

程式碼 **MIT**（見 [`LICENSE`](LICENSE)）。第三方詞庫各依原始授權，見 `THIRD_PARTY_LICENSES.md`。

## 🙌 貢獻 · Contributing

歡迎 PR 補充台灣慣用語 / 修正配對 / 回報誤判 —— 請先讀 [`CONTRIBUTING.md`](CONTRIBUTING.md)（四級判定原則、詞庫結構、請勿 PR 授權受限資料）。
也可直接開 Issue：**誤判回報** 或 **新增/修正支語**（已附範本）。結構與分級邏輯見 [`SKILL.md`](SKILL.md)，案例見 [`references/cases.md`](references/cases.md)。

---

<sub>Keywords: 支語 · 支語警察 · 台灣用語 · 繁體中文 · Taiwanese Mandarin · Traditional Chinese · 中國用語對照 · cross-strait vocabulary · Claude Code skill · Codex · Cursor · NLP</sub>
