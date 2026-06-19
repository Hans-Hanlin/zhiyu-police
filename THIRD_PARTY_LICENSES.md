# Third-Party Licenses / 第三方詞庫授權

`references/taiwanizer_dict.json`（公開核心詞庫）的條目衍生自下列來源。每筆條目都帶 `source` 欄位可稽核。

## 已內建（授權允許再散布）

| source 欄位 | 來源專案 | 授權 | 原始 URL |
|---|---|---|---|
| `opencc-IT`, `opencc-TW` | BYVoid/OpenCC（TWPhrases / TWPhrasesIT）| Apache-2.0 | https://github.com/BYVoid/OpenCC |
| `支語檢查器` | AKuKu-Taiwan/StopChLang_Dictionary | MIT | https://github.com/AKuKu-Taiwan/StopChLang_Dictionary |
| `cn2tw` | PJCHENder/cn2tw4programmer | ISC | https://github.com/PJCHENder/cn2tw4programmer |
| `aronhack` | aronhack/Chinese-Vocabulary-Radar | CC0-1.0 | https://github.com/aronhack/Chinese-Vocabulary-Radar |
| `curated`, `策展-AIcoding`, `curated-name`, `reviewed`, （無 source）| 本專案自有策展 | 本 repo MIT | — |

各來源的完整授權條款請見其原始 repo。本專案依各授權保留出處標示。

## 未內建（授權受限，使用者本機自取）

下列來源**不隨本 repo 散布**；如需擴充，請在本機執行 `scripts/ingest_*.py` 自行取得，並自負授權責任：

| 來源 | 授權 | 為何不散布 |
|---|---|---|
| g0v/moedict-data-csld（中華語文知識庫 / 兩岸詞典）| CC BY-NC-ND 4.0 | 禁改作（ND）、禁商用（NC）——不可公開散布衍生詞庫 |
| 國家教育研究院 樂詞網（兩岸對照名詞 / 一般名詞 / 學術領域）| 政府資料，授權未逐項確認 | 保守起見不散布；使用者自取時請確認各資料集授權並標示出處 |

> 若你是上述來源的權利人、或認為本專案有任何授權標示疏漏，歡迎開 issue 指正，我們會立即處理。
