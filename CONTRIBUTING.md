# 貢獻指南 · Contributing to 支語警察

歡迎一起讓台灣的中文更道地！最有價值的貢獻是：**補新支語、修錯配對、回報誤判**。

## 核心原則（請先讀）· Core principle

> **寧可漏抓，不要錯抓。** 把一個台灣本來就用的詞誤判成支語，比漏掉一個支語更糟。

支語警察的價值在「**精準**」，不在「抓得多」。請務必分清下面四級。

## 詞庫結構 · Dictionary structure

詞庫在 [`references/taiwanizer_dict.json`](references/taiwanizer_dict.json)，四個分級：

| 級別 | 意義 | 行為 | 例 |
|------|------|------|----|
| `hard` | 台灣基本不用的明確支語 | **自動改正** | 軟件→軟體、視頻→影片 |
| `grey` | 台灣也用 / 已融入 / 語境敏感 | **只提示，請使用者校對** | 迭代、優化、數據 |
| `context` | 兩岸**同字不同義**的假朋友 | **絕不自動改，只提示看語境** | 土豆（台=花生/陸=馬鈴薯）|
| `whitelist` | 看似支語、其實台灣本來就用 | **絕不抓** | 社群、渲染、部署、資訊 |

每筆條目格式：`{"zh": "支語", "tw": ["台灣詞1","台灣詞2"], "note": "說明", "source": "出處"}`

## 怎麼貢獻 · How to contribute

### A. 開 Issue（最簡單）
- **誤判**：支語警察把台灣詞當成支語 → 開「誤判回報」issue。
- **建議新增 / 修正**：想加一個支語、或某個配對是錯的 → 開「新增/修正支語」issue。

### B. 直接送 PR
1. 編輯 `references/taiwanizer_dict.json`，依上面四級放對位置；或用內建工具：
   ```bash
   python scripts/learn.py whitelist <詞>      # 標白名單（誤判）
   python scripts/learn.py promote <詞>        # 升級硬錯
   python scripts/learn.py context <詞> "說明" # 標同名異實
   python scripts/learn.py fix <詞> <台灣詞>   # 修配對
   ```
2. **實測**：`python scripts/police.py 一段測試文.txt`，確認新詞有抓到、且**沒誤抓常用台灣詞**。
3. **附依據**：新增支語請在 PR 說明來源（教育部辭典、維基兩岸對照、實際用例…）。
4. 送 PR。

### ⚠️ 請勿 PR 這些
- **授權受限資料**：g0v csld（CC BY-NC-ND）、國教院 NAER（政府資料）的整批詞——這些只能在本機用 `ingest_*.py` 自取，不可進公開 repo（見 `THIRD_PARTY_LICENSES.md`）。
- **超冷僻專業 jargon 整批匯入**：會拖慢又增誤判；專業領域屬 ULTRA 層，請走 `ingest_naer_domains.py --sci` 本機擴充。
- **政治 / 國名譯名爭議詞**：本工具聚焦寫作用語，不碰政治。

## 判斷拿不準時 · When unsure
丟進 `grey`（請人校對），不要丟 `hard`。灰色地帶交給使用者決定，是最安全的選擇。
更多分級邏輯與真實案例見 [`SKILL.md`](SKILL.md) 與 [`references/cases.md`](references/cases.md)。

謝謝你讓台灣的中文保持台灣味 🙏
