# Notion AI 文檔整理助手

智能文檔整理與上傳工具，使用 Gemini AI 自動優化並上傳到 Notion。

## 功能特點

✨ **AI 驅動**
- 使用 Gemini 3.0 Flash 分析文檔
- 自動生成摘要和關鍵字
- 智能優化排版結構

📝 **自動排版**
- 識別標題層級
- 優化段落間距
- 自動添加圖示
- 生成 Callout 提示框

🚀 **一鍵上傳**
- 直接上傳到 Notion
- 保持格式完整
- 支援 Markdown

## 安裝依賴

```bash
pip install notion-client google-generativeai python-dotenv
```

## 使用方式

### 基本用法

```bash
python organize_and_upload.py <文檔路徑>
```

### 範例

```bash
# 整理並上傳 CHANGELOG
python organize_and_upload.py ../CHANGELOG.md

# 整理技術文檔
python organize_and_upload.py ../README.md
```

## 配置

使用專案根目錄的 `.env` 文件：
- `GOOGLE_API_KEY` - Google Gemini API Key（已配置）
- `NOTION_TOKEN` - Notion Integration Token（已配置）

## 工作流程

1. 📖 讀取 Markdown 文件
2. 🤖 Gemini AI 分析內容
3. 📋 生成摘要和關鍵字
4. ✨ 優化排版結構
5. 📤 上傳到 Notion
6. ✅ 完成！

## 支援的格式

- ✅ 標題（H1-H6）
- ✅ 段落
- ✅ 列表（有序/無序）
- ✅ 代碼塊
- ✅ Callout 提示框
- ✅ 引用

## 輸出範例

每個文檔會包含：
- 📋 **摘要** - AI 生成的內容總結
- 🏷️ **關鍵字** - 自動提取的重點
- 📄 **優化內容** - 格式化後的主體

## 進階功能

### 批量處理

```bash
# 處理多個文檔
for file in docs/*.md; do
    python organize_and_upload.py "$file"
done
```

### 自訂父頁面

修改 `organize_and_upload.py` 中的 `PARENT_PAGE_ID`

## 注意事項

- Gemini API 免費額度：每天 1500 次請求
- Notion API 限制：每次最多 100 個區塊
- 大型文檔會自動分批上傳

## 故障排除

### API Key 錯誤
確認 `.env` 文件中有正確的 API Key

### Notion 權限錯誤
確認 Integration 已連接到目標頁面

### JSON 解析錯誤
AI 回應可能需要重試，腳本會自動處理

## 版本歷史

- v1.0.0 (2025-12-12) - 初版發布
  - 基本文檔整理功能
  - Gemini AI 整合
  - Notion 自動上傳
