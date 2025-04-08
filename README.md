# 台灣旅遊助手

一個使用RAG技術的台灣旅遊景點助手。系統可以根據用戶需求，透過檢索詳細的景點資料，提供從簡單景點查詢到完整客製化行程規劃的全方位旅遊服務，涵蓋台灣各地景點推薦、美食指南、交通建議與多日遊行程安排。

## 安裝與配置

### 前置需求
- Docker 

### API 金鑰註冊
- 請至 [Google AI Studio](https://aistudio.google.com/apikey) 註冊 Gemini API Key
- 請至 [Cohere](https://dashboard.cohere.com/api-keys) 註冊 Cohere API KEY


### 環境設定
1. clone專案或下載原始碼
2. 在 `backend/app/` 中建立.env檔案
3. 在 `backend/app/.env` 中設定 API 金鑰以及自訂的model_name(Gemini)、secret_key(可為任意字串)：
   ```
   gemini_api_key="YOUR_GEMINI_API_KEY" 
   cohere_api_key="YOUR_COHERE_API_KEY"
   model_name="gemini-2.0-flash"
   secret_key="jwtsecretkey"
   ```

## 運行方式

### 使用 Docker
```bash
# 先進入專案資料夾，構建所有容器，需要一點時間
docker-compose build

# 啟動所有容器，可使用瀏覽器查看
docker-compose up -d

# 停止所有容器
docker-compose down

```

### 使用系統
1. 開啟瀏覽器訪問 http://localhost   (後端初始化會需要一點時間，詳細狀況請看container logs)
2. 請先註冊或登入系統
3. 在輸入框中輸入您的商品需求，例如：「我想去陽明山一日遊，請問有哪些推薦的景點?」
4. 點擊「送出」按鈕，系統將開始處理您的請求
5. 稍等片刻，系統將產生景點資訊


##   評估RAG
專案目錄eval_rag可在langsmith上評估RAG回復品質
### 前置需求
- python 3.12.7
- `pip install -r requirements.txt`
### API 金鑰註冊
請至 [langsmith](https://smith.langchain.com/settings) 註冊API key
### 環境設定
1. clone專案或下載原始碼
2. 在 `eval_rag/` 中建立.env檔案
3. 在 `eval_rag/.env` 中設定 API 金鑰以及自訂的model_name(Gemini)、secret_key(可為任意字串)：
   ```
   gemini_api_key="YOUR_GEMINI_API_KEY" 
   langsmith_api_key="YOUR_LANGSMITH_API_KEY"
   model_name="gemini-2.0-flash"
   ```
## 運行方式
進入專案資料夾
`cd eval_rag/` 
執行`rag_eval.py` 
`python rag_eval.py`
