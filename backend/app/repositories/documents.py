from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_document(
        self,
        source_id: int,
        uri: str,
        title: str,
        content_hash: str,
        mime_type: str,
    ) -> Document:
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
        return self.session.get(Document, document_id)

    def update_document_status(self, document_id: int, status: str) -> Optional[Document]:
        document = self.get_document(document_id)
        if document is None:
            return None

        document.status = status
        document.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(document)
        return document
