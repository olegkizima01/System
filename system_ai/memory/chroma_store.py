import os
from typing import Any, List, Optional


class ChromaStore:
    def __init__(self, persist_dir: str) -> None:
        self.persist_dir = os.path.expanduser(persist_dir)
        self._store: Any = None

    def _ensure(self) -> bool:
        if self._store is not None:
            return True
        try:
            from langchain_chroma import Chroma
            from langchain_huggingface import HuggingFaceEmbeddings

            os.makedirs(self.persist_dir, exist_ok=True)
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            self._store = Chroma(persist_directory=self.persist_dir, embedding_function=embeddings)
            return True
        except Exception:
            self._store = None
            return False

    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> bool:
        if not self._ensure():
            return False
        try:
            self._store.add_texts(texts=texts, metadatas=metadatas)
            return True
        except Exception:
            return False

    def similarity_search(self, query: str, k: int = 5) -> List[Any]:
        if not self._ensure():
            return []
        try:
            return self._store.similarity_search(query, k=k)
        except Exception:
            return []
