from typing import List
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

class LocalRAGEngine:
    """In-memory vector store for analyzing large 10-K text sections."""

    def __init__(self, model_name: str = "nomic-embed-text"):
        self.embeddings = OllamaEmbeddings(model=model_name)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )

    def query_document_section(self, raw_text: str, query: str, top_k: int = 3) -> List[str]:
        """Splits raw SEC text, embeds into an ephemeral Chroma collection, and retrieves relevant chunks."""
        docs = [Document(page_content=raw_text)]
        splits = self.text_splitter.split_documents(docs)
        
        vectorstore = Chroma.from_documents(
            documents=splits, 
            embedding=self.embeddings
        )
        
        results = vectorstore.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]