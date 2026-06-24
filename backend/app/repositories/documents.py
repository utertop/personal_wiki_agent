from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document


class DocumentRepository:
    """封装 Document 和 Chunk 的基础读写操作，供索引流程复用。"""

    def __init__(self, session: Session) -> None:
        """保存当前请求或任务使用的数据库 session。"""
        self.session = session

    def create_document(
        self,
        source_id: int,
        uri: str,
        title: str,
        content_hash: str,
        mime_type: str,
    ) -> Document:
        """创建一个标准文档记录，后续 parser 和 chunker 会围绕它继续处理。"""
        document = Document(
            source_id=source_id,
            uri=uri,
            title=title,
            content_hash=content_hash,
            mime_type=mime_type,
        )
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def create_chunk(
        self,
        document_id: int,
        chunk_index: int,
        text: str,
        heading_path: Optional[str],
        page_number: Optional[int],
        token_count: int,
    ) -> Chunk:
        """为指定文档创建一个 chunk 记录，保留定位和 token 统计信息。"""
        chunk = Chunk(
            document_id=document_id,
            chunk_index=chunk_index,
            text=text,
            heading_path=heading_path,
            page_number=page_number,
            token_count=token_count,
        )
        self.session.add(chunk)
        self.session.commit()
        self.session.refresh(chunk)
        return chunk

    def get_document(self, document_id: int) -> Optional[Document]:
        """按主键查询文档；不存在时返回 None。"""
        return self.session.get(Document, document_id)

    def update_document_status(self, document_id: int, status: str) -> Optional[Document]:
        """更新文档状态，例如把缺失文件标记为 deleted。"""
        document = self.get_document(document_id)
        if document is None:
            return None

        document.status = status
        document.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(document)
        return document
