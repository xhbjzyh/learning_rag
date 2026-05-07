import pytest
from core.embedder import embeder
from core.rag_engine import rag_engine

def test_embedder_load():
    """测试向量化模型是否成功加载"""
    # 检查模型是否初始化
    assert embeder is not None
    # 检查向量维度是否正确
    assert embeder.embedding_dim == 512

def test_single_text_embedding():
    """测试单文本向量化"""
    text = "这是一个测试文本"
    vector = embeder.embed_text(text)
    # 检查向量形状
    assert vector.shape == (512,)

def test_rag_search_empty():
    """测试空知识库检索"""
    # 注意：如果你的FAISS索引是空的，会抛出业务异常
    with pytest.raises(Exception):
        rag_engine.search("什么是RAG？")