import os
import json
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from core.config import TOP_K_RESULTS, GEMINI_API_KEY, BASE_DIR

FAISS_PATH = os.path.join(BASE_DIR, "faiss_store")


class VectorStore:
    def __init__(self):
        print("Initializing FAISS vector store...")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=GEMINI_API_KEY
        )
        self.store = None
        self._load()
        print("FAISS ready!")

    def add(self, text: str, timestamp: str):
        try:
            if self.store is None:
                self.store = FAISS.from_texts(
                    texts=[text],
                    embedding=self.embeddings,
                    metadatas=[{"timestamp": timestamp}]
                )
            else:
                self.store.add_texts(
                    texts=[text],
                    metadatas=[{"timestamp": timestamp}]
                )
            self.store.save_local(FAISS_PATH)
        except Exception:
            pass

    def search(self, query: str, top_k: int = TOP_K_RESULTS):
        if self.store is None:
            return []
        try:
            results = self.store.similarity_search(query, k=top_k)
            return [doc.page_content for doc in results]
        except Exception:
            return []

    def _load(self):
        if os.path.exists(FAISS_PATH):
            try:
                self.store = FAISS.load_local(
                    FAISS_PATH,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("Previous vectors loaded!")
            except Exception:
                self.store = None