
"""
BM25检索引擎
实现基于关键词的全文检索，与FAISS向量检索形成互补

论文第2.1.2节、2.2.2节、4.2.1节实现：
- 并行执行向量检索（语义）和BM25检索（关键词）
- 加权融合两种检索结果
"""
import math
from typing import List, Dict, Tuple
from collections import defaultdict
from utils.logger import logger


class BM25Retriever:
    """BM25全文检索引擎"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化BM25检索器
        
        Args:
            k1: 词频饱和参数，控制词频的影响程度（默认1.5）
            b: 长度归一化参数，控制文档长度的影响（默认0.75）
        """
        self.k1 = k1
        self.b = b
        self.doc_freq = defaultdict(int)  # 包含某词的文档数
        self.doc_lengths = {}  # 文档ID -> 文档长度（分词数）
        self.avg_doc_length = 0  # 平均文档长度
        self.total_docs = 0  # 总文档数
        self.idf_cache = {}  # IDF缓存
        
        # 存储文档内容
        self.documents = {}
        
        logger.info(f"✅ BM25检索器初始化完成 (k1={k1}, b={b})")

    def _tokenize(self, text: str) -> List[str]:
        """
        文本分词（简化版，使用空格分隔）
        
        🔥 如果安装了jieba，会自动使用jieba进行中文分词
        """
        try:
            # 尝试使用jieba分词
            import jieba
            tokens = list(jieba.cut_for_search(text))
            return [t.lower() for t in tokens if t.strip()]
        except ImportError:
            # 如果没有jieba，使用简单的空格分词
            logger.warning("⚠️ 未检测到jieba库，使用简单空格分词（效果可能不佳）")
            logger.warning("💡 建议运行: pip install jieba")
            return text.lower().split()

    def add_document(self, doc_id: int, content: str):
        """
        添加文档到索引
        
        Args:
            doc_id: 文档ID
            content: 文档内容
        """
        # 中文分词
        tokens = self._tokenize(content)
        
        # 更新统计信息
        self.documents[doc_id] = {
            'content': content,
            'tokens': tokens
        }
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs += 1
        
        # 更新文档频率
        unique_tokens = set(tokens)
        for token in unique_tokens:
            self.doc_freq[token] += 1
        
        # 更新平均文档长度
        self.avg_doc_length = sum(self.doc_lengths.values()) / self.total_docs
        
        # 清除IDF缓存
        self.idf_cache.clear()

    def add_documents_batch(self, documents: List[Dict]):
        """
        批量添加文档
        
        Args:
            documents: [{'id': int, 'content': str}, ...]
        """
        for doc in documents:
            self.add_document(doc['id'], doc['content'])
        
        logger.info(f"📝 批量添加 {len(documents)} 个文档，总计 {self.total_docs} 个文档")

    def _calc_idf(self, term: str) -> float:
        """
        计算IDF值（逆文档频率）
        
        公式：IDF(t) = log((N - n(t) + 0.5) / (n(t) + 0.5))
        其中N是总文档数，n(t)是包含词t的文档数
        """
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        n_t = self.doc_freq.get(term, 0)
        idf = math.log((self.total_docs - n_t + 0.5) / (n_t + 0.5) + 1e-6)
        
        # IDF至少为0
        idf = max(0, idf)
        
        self.idf_cache[term] = idf
        return idf

    def _calc_bm25_score(self, query_tokens: List[str], doc_id: int) -> float:
        """
        计算查询与文档的BM25得分
        
        公式：BM25(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
        """
        if doc_id not in self.documents:
            return 0.0
        
        doc_tokens = self.documents[doc_id]['tokens']
        doc_len = self.doc_lengths[doc_id]
        
        score = 0.0
        term_freq = defaultdict(int)
        
        # 计算词频
        for token in doc_tokens:
            term_freq[token] += 1
        
        # 计算BM25得分
        for token in query_tokens:
            if token not in term_freq:
                continue
            
            tf = term_freq[token]
            idf = self._calc_idf(token)
            
            # BM25公式
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
            
            if denominator > 0:
                score += idf * (numerator / denominator)
        
        return score

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        BM25检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索结果列表，按得分降序排列
        """
        if self.total_docs == 0:
            logger.warning("⚠️ BM25索引为空")
            return []
        
        # 查询分词
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            return []
        
        # 计算所有文档的BM25得分
        scores = []
        for doc_id in self.documents.keys():
            score = self._calc_bm25_score(query_tokens, doc_id)
            if score > 0:
                scores.append({
                    'doc_id': doc_id,
                    'bm25_score': score,
                    'content': self.documents[doc_id]['content']
                })
        
        # 按得分排序
        scores.sort(key=lambda x: x['bm25_score'], reverse=True)
        
        # 返回top_k
        results = scores[:top_k]
        
        logger.info(f"🔍 BM25检索: '{query[:30]}...', 返回 {len(results)} 个结果")
        
        return results

    def rebuild_index(self, documents: List[Dict]):
        """
        重建索引（清空并重新添加）
        
        Args:
            documents: [{'id': int, 'content': str}, ...]
        """
        # 清空所有数据
        self.documents.clear()
        self.doc_freq.clear()
        self.doc_lengths.clear()
        self.idf_cache.clear()
        self.total_docs = 0
        self.avg_doc_length = 0
        
        # 重新添加
        self.add_documents_batch(documents)
        
        logger.info(f"🔄 BM25索引重建完成，共 {self.total_docs} 个文档")


# 全局单例
bm25_retriever = BM25Retriever()
