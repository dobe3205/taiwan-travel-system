from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.rate_limiters import InMemoryRateLimiter
import torch
import os
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TravelRAGService:
    """
    台灣旅遊RAG系統，用於處理旅遊相關查詢
    整合了向量檢索和語言模型生成
    """
    
    def __init__(self, gemini_api_key, **kwargs):
        """
        初始化台灣旅遊RAG服務
        
        Args:
            gemini_api_key: Google Gemini API金鑰
            **kwargs: 其它參數（保留以保持與舊介面兼容）
        """
        # 設置環境變數
        os.environ["GOOGLE_API_KEY"] = gemini_api_key
        
        # 設置資源路徑
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        
        # 設置向量資料庫存放位置
        self.persist_directory = os.path.join(backend_dir, "chroma_db")
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 設置資料檔案路徑
        self.data_path = os.path.join(backend_dir, "data", "attractions.csv")
        
        # 檢查備用路徑
        if not os.path.exists(self.data_path):
            project_dir = os.path.dirname(backend_dir)
            self.data_path = os.path.join(project_dir, "data", "attractions.csv")
            
        if not os.path.exists(self.data_path):
            logger.warning(f"找不到資料檔案: attractions.csv")
            
        # 設定設備
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"使用設備: {self.device}")
        
        # 設定速率限制
        self.rate_limiter = InMemoryRateLimiter(
            requests_per_second=0.05,  
            check_every_n_seconds=0.1,  
            max_bucket_size=10,  
        )
        
        # 設定嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-small",
            model_kwargs={
                'device': self.device
            },  
            encode_kwargs={
                'normalize_embeddings': True
            }
        )
        
        # 設定語言模型
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            temperature=0.2, 
            rate_limiter=self.rate_limiter
        )
        
        # 初始化其他組件
        self.documents = None
        self.vector_store = None
        self.retriever = None
        self.qa_chain = None
        
        # 初始化系統
        self.initialize_system()
    
    def load_documents(self):
        """載入資料文件"""
        if not os.path.exists(self.data_path):
            logger.error(f"資料檔案不存在: {self.data_path}")
            return None
            
        try:
            # 根據檔案類型選擇合適的載入器
            if self.data_path.endswith('.csv'):
                loader = CSVLoader(self.data_path, encoding='utf-8')
            elif self.data_path.endswith('.pdf'):
                loader = PyPDFLoader(self.data_path)
            elif self.data_path.endswith('.txt'):
                loader = TextLoader(self.data_path, encoding='utf-8')
            else:
                logger.error(f"不支援的檔案格式: {self.data_path}")
                return None
                
            # 載入文件
            documents = loader.load()
            logger.info(f"成功載入 {len(documents)} 個文件從 {self.data_path}")
            self.documents = documents
            return documents
            
        except Exception as e:
            logger.error(f"載入文件時出錯: {str(e)}")
            return None
    
    def split_documents(self, documents, chunk_size=300, chunk_overlap=50):
        """將文件分割為更小的塊"""
        if not documents:
            return []
            
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "，", " ", ""]
        )
        
        splits = text_splitter.split_documents(documents)
        logger.info(f"文件已分割: {len(splits)} 個區塊")
        return splits
    
    def create_vector_store(self, documents):
        """創建向量資料庫"""
        if not documents:
            logger.error("沒有文件可以創建向量資料庫")
            return None
            
        try:
            # 創建向量資料庫
            vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            logger.info(f"向量資料庫已建立並保存至 {self.persist_directory}")
            self.vector_store = vector_store
            return vector_store
            
        except Exception as e:
            logger.error(f"創建向量資料庫時出錯: {str(e)}")
            return None
    
    def load_vector_store(self):
        """載入現有的向量資料庫"""
        if os.path.exists(self.persist_directory):
            try:
                vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                
                logger.info(f"已從 {self.persist_directory} 載入向量資料庫")
                self.vector_store = vector_store
                return vector_store
                
            except Exception as e:
                logger.error(f"載入向量資料庫時出錯: {str(e)}")
                return None
        else:
            logger.warning(f"向量資料庫 {self.persist_directory} 不存在")
            return None
    
    def setup_retriever(self):
        """設置檢索器"""
        if not self.vector_store:
            logger.error("沒有向量資料庫，無法設置檢索器")
            return None
            
        if not self.documents:
            logger.warning("沒有原始文件，只能使用向量相似度檢索")
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={'k': 5}
            )
            return self.retriever
        
        try:
            # 設置向量相似度檢索器
            sim_retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={'k': 5}
            )
            
            # 設置BM25檢索器
            bm25_retriever = BM25Retriever.from_documents(
                documents=self.documents,
                k=5
            )
            
            # 組合檢索器
            ensemble_retriever = EnsembleRetriever(
                retrievers=[sim_retriever, bm25_retriever],
                weights=[0.8, 0.2]
            )
            
            # 設置多查詢檢索器
            multi_retriever = MultiQueryRetriever.from_llm(
                llm=self.llm,
                retriever=ensemble_retriever
            )
            
            logger.info("檢索器設置完成")
            self.retriever = multi_retriever
            return self.retriever
            
        except Exception as e:
            logger.error(f"設置檢索器時出錯: {str(e)}")
            
            # 如果組合檢索器設置失敗，回退到簡單檢索器
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={'k': 5}
            )
            return self.retriever
    
    def setup_qa_chain(self):
        """設置問答鏈"""
        if not self.retriever:
            logger.error("沒有檢索器，無法設置問答鏈")
            return None
            
        try:
            # 設置提示模板
            template = """
            你是一位臺灣旅遊專家，請基於以下資訊回答用戶的旅遊相關問題。
            如果你不知道答案，請直接說你不知道，不要編造資訊。
            
            資訊:
            {context}
            
            用戶問題: {question}
            
            請提供詳細、有幫助且符合臺灣當地文化的回答，並盡可能給予具體的建議。
            如果有多個選擇，請根據場景、用戶喜好和地點的受歡迎程度進行推薦。
            """
            
            prompt = PromptTemplate(
                template=template,
                input_variables=["context", "question"]
            )
            
            # 創建QA鏈
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": prompt}
            )
            
            logger.info("問答鏈設置完成")
            self.qa_chain = qa_chain
            return qa_chain
            
        except Exception as e:
            logger.error(f"設置問答鏈時出錯: {str(e)}")
            return None
    
    def initialize_system(self):
        """初始化整個系統，自動檢測是否存在向量資料庫"""
        try:
            # 檢查向量資料庫是否已存在
            db_exists = os.path.exists(self.persist_directory) and os.listdir(self.persist_directory)
            
            if db_exists:
                logger.info("檢測到現有向量資料庫，嘗試載入...")
                # 嘗試載入現有向量資料庫
                if self.load_vector_store():
                    # 不管是否成功載入文件，我們都加載一次保險
                    self.documents = self.load_documents()
                    # 設置檢索器和問答鏈
                    self.setup_retriever()
                    self.setup_qa_chain()
                    logger.info("成功載入現有向量資料庫")
                    return True
                else:
                    logger.warning("現有向量資料庫無法載入，將創建新的資料庫")
                    db_exists = False
            
            # 如果不存在向量資料庫或載入失敗，創建新的
            if not db_exists:
                # 載入文件
                documents = self.load_documents()
                if not documents:
                    logger.error("無法載入文件，系統初始化失敗")
                    return False
                
                # 分割文件
                splits = self.split_documents(documents)
                
                # 創建向量資料庫
                if not self.create_vector_store(splits):
                    logger.error("創建向量資料庫失敗")
                    return False
                
                # 設置檢索器和問答鏈
                self.setup_retriever()
                self.setup_qa_chain()
                logger.info("成功創建新的向量資料庫")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"初始化系統時發生錯誤: {str(e)}")
            return False
    
    def process_query(self, query):
        """處理用戶查詢"""
        if not self.qa_chain:
            logger.error("問答鏈未設置")
            return "系統錯誤：問答鏈未設置"
        
        try:
            # 處理查詢
            result = self.qa_chain.invoke({"query": query})
            answer = result["result"]
            retrieved_docs = result.get("source_documents", [])
            
            # 顯示檢索到的文檔（用於日誌）
            for i, doc in enumerate(retrieved_docs):
                logger.info(f"檢索到文檔 {i+1}:")
                logger.info(f"內容: {doc.page_content[:150]}...")
                logger.info(f"來源: {doc.metadata.get('source', '未知')}")
            
            return answer
            
        except Exception as e:
            logger.error(f"處理查詢時發生錯誤: {str(e)}")
            return f"處理查詢時發生錯誤: {str(e)}"
    
    def process_product_comparison(self, user_query):
        """
        處理用戶旅遊查詢請求
        Args:
            user_query: 用戶的查詢字串
            
        Returns:
            tuple: (原始回應文字, JSON字典)
        """
        try:
            # 處理查詢
            response = self.process_query(user_query)
            
            # 返回原始回應和簡單的JSON格式
            return response, {"response": response}
            
        except Exception as e:
            error_msg = f"處理查詢出錯: {str(e)}"
            logger.error(error_msg)
            return error_msg, {"error": error_msg}
