"""
文档解析工具
支持解析TXT、PDF、DOCX格式的文档，提取文本内容
"""
"""
文档解析工具
支持解析TXT、PDF、DOCX格式的文档，提取文本内容
"""
import os
import hashlib
from typing import List, Dict
from utils.logger import logger


def calculate_md5(file_content: bytes) -> str:
    """
    计算文件内容的MD5哈希值
    :param file_content: 文件二进制内容
    :return: MD5哈希值（32位小写）
    """
    md5_hash = hashlib.md5()
    md5_hash.update(file_content)
    return md5_hash.hexdigest()


# ... 保留原有的 DocumentParser 类 ...
import os
from typing import List, Dict
from utils.logger import logger


class DocumentParser:
    """文档解析器"""

    @staticmethod
    def parse_txt(file_path: str) -> str:
        """
        解析TXT文件
        :param file_path: 文件路径
        :return: 文本内容
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"TXT文件解析成功: {file_path}")
            return content
        except Exception as e:
            logger.error(f"TXT文件解析失败: {file_path}, 错误: {str(e)}")
            raise Exception("TXT文件解析失败")

    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """
        解析PDF文件
        :param file_path: 文件路径
        :return: 文本内容
        """
        try:
            # 尝试使用PyPDF2解析
            try:
                import PyPDF2
                content = ""
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        content += page.extract_text() + "\n"
                logger.info(f"PDF文件解析成功: {file_path}")
                return content
            except ImportError:
                logger.warning("PyPDF2未安装，PDF解析功能不可用")
                raise Exception("请先安装PyPDF2: pip install PyPDF2")
        except Exception as e:
            logger.error(f"PDF文件解析失败: {file_path}, 错误: {str(e)}")
            raise Exception("PDF文件解析失败")

    @staticmethod
    def parse_docx(file_path: str) -> str:
        """
        解析DOCX文件
        :param file_path: 文件路径
        :return: 文本内容
        """
        try:
            try:
                from docx import Document
                doc = Document(file_path)
                content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                logger.info(f"DOCX文件解析成功: {file_path}")
                return content
            except ImportError:
                logger.warning("python-docx未安装，DOCX解析功能不可用")
                raise Exception("请先安装python-docx: pip install python-docx")
        except Exception as e:
            logger.error(f"DOCX文件解析失败: {file_path}, 错误: {str(e)}")
            raise Exception("DOCX文件解析失败")

    @staticmethod
    def parse_document(file_path: str, file_type: str) -> str:
        """
        统一解析入口
        :param file_path: 文件路径
        :param file_type: 文件类型
        :return: 文本内容
        """
        if file_type == "txt":
            return DocumentParser.parse_txt(file_path)
        elif file_type == "pdf":
            return DocumentParser.parse_pdf(file_path)
        elif file_type == "docx":
            return DocumentParser.parse_docx(file_path)
        else:
            raise Exception(f"不支持的文件类型: {file_type}")

    @staticmethod
    def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        将长文本切分为固定大小的块（用于向量化）
        【安全版】：无死循环、严格递增、内存安全
        :param text: 原始文本
        :param chunk_size: 每块的大小（字符数）
        :param overlap: 块之间的重叠大小
        :return: 文本块列表
        """
        chunks = []
        start = 0
        text_length = len(text)

        # 防御性编程：如果文本为空，直接返回空列表
        if text_length == 0:
            logger.info("文本为空，无需切分")
            return chunks

        # 防御性编程：确保overlap小于chunk_size，避免逻辑错误
        if overlap >= chunk_size:
            overlap = chunk_size // 10  # 重叠设为块大小的10%

        while start < text_length:
            # 计算当前块的结束位置
            end = min(start + chunk_size, text_length)

            # 切分块
            chunk = text[start:end].strip()

            # 只保留非空块
            if chunk:
                chunks.append(chunk)

            # 【关键修复】：计算下一个start
            next_start = end - overlap

            # 【核心防死循环逻辑】：
            # 如果 next_start 没有超过当前 start，说明已经到末尾，直接跳出
            # 或者如果 next_start >= text_length，也直接跳出
            if next_start <= start or next_start >= text_length:
                break

            # 更新start
            start = next_start

        logger.info(f"文本切分完成，共 {len(chunks)} 个块")
        return chunks


# 全局单例
document_parser = DocumentParser()