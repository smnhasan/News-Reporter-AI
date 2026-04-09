from typing import List
from chromadb import Settings
from langchain_community.vectorstores import Chroma
from ..models.embedding_model import Embedding

import sys
print(f'Sys Path: {sys.path}')



class VectorStore:
    def __init__(self):
        self.embedding_model = Embedding()
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.dir = os.path.join(current_dir, "knowledge_base")
        self.settings = Settings(
            anonymized_telemetry=False,
            is_persistent=True,
            persist_directory=self.dir,
        )
        self.db = self._create_collection(
            embedding=self.embedding_model,
            dir=self.dir,
            settings=self.settings
        )

    def _create_collection(self, embedding, dir: str, settings: Settings):
        try:
            db = Chroma(
                persist_directory=dir,
                client_settings=settings,
                embedding_function=embedding,
                collection_metadata={
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 400,
                    "hnsw:search_ef": 400,
                    "hnsw:M": 128,
                    "hnsw:resize_factor": 2.0,
                },
            )
            # print(f"Number of documents in collection: {db.count()}", flush=True)
            return db
        except Exception as e:
            print(f"Error creating collection: {str(e)}")
            raise

    def query(self, query: str) -> List[str]:
        """
        Retrieve relevant documents based on the query.
        
        Args:
            query (str): The search query to find relevant documents.
        
        Returns:
            List[str]: A list of documents that match the query.
        """
        try:
            results = self.db.similarity_search_with_relevance_scores(
                query=query,
                k=11
            )
            print(f'Retrieved {len(results)} documents for query: {query}', flush=True)
            return results if results else []
        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")
            return []

    def add(self, documents: List[str]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents (List[str]): A list of documents to be added.
        """
        try:
            self.db.add_documents(documents=documents)
            print(f"Added {len(documents)} documents to the collection")
        except Exception as e:
            print(f"Error adding documents: {str(e)}")
            raise

    def delete(self, document_ids: List[str]) -> None:
        """
        Delete documents from the vector store.
        
        Args:
            document_ids (List[str]): A list of document IDs to be deleted.
        """
        try:
            self.db.delete(ids=document_ids)
            print(f"Deleted {len(document_ids)} documents from the collection")
        except Exception as e:
            print(f"Error deleting documents: {str(e)}")
            raise

    def update(self, documents: List[str]) -> None:
        """
        Update existing documents in the vector store.
        
        Args:
            documents (List[str]): A list of documents to be updated.
        """
        try:
            document_ids = [f"doc_{i}" for i in range(len(documents))]
            self.db.upsert(
                documents=documents,
                ids=document_ids
            )
            print(f"Updated {len(documents)} documents in the collection")
        except Exception as e:
            print(f"Error updating documents: {str(e)}")
            raise
        
        