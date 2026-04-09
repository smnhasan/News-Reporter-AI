import logging
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .db.vectorstore import VectorStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        """
        Initialize the Retriever with a VectorStore instance.

        Raises:
            RuntimeError: If VectorStore initialization fails.
        """
        logger.info("Initializing Retriever with VectorStore")
        try:
            self.vector_store = VectorStore()
            self.text_splitter = self.create_text_splitter()
        except Exception as e:
            logger.error(f"Failed to initialize Retriever: {str(e)}")
            raise RuntimeError(f"Retriever initialization failed: {str(e)}") from e
        
  
    def retrieve(self, query: str) -> tuple[str, List[str]]:
        """
        Retrieve relevant documents based on the query using the vector store.

        Args:
            query (str): The search query to find relevant documents.

        Returns:
            List[str]: A list of documents that match the query.

        Raises:
            ValueError: If the query is empty or invalid.
            RuntimeError: If the vector store query fails.
        """
        if not query or not isinstance(query, str):
            logger.error("Invalid query: Query must be a non-empty string")
            raise ValueError("Query must be a non-empty string")

        logger.info(f"Retrieving documents for query: {query}")
        try:
            results = self.vector_store.query(query)
            logger.info(f"Retrieved {len(results)} documents")
            
            context, url_map = self.prepare_context(results)
            return context, url_map
        except Exception as e:
            logger.error(f"Failed to retrieve documents for query '{query}': {str(e)}")
            raise RuntimeError(f"Document retrieval failed: {str(e)}") from e


    def ingest(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store.

        Args:
            documents (List[Document]): A list of LangChain Document objects.

        Raises:
            ValueError: If documents list is empty or contains invalid entries.
            RuntimeError: If document ingestion fails.
        """
        if not documents or not isinstance(documents, list):
            logger.error("Invalid documents: Must provide a non-empty list of Document objects")
            raise ValueError("Documents must be a non-empty list of Document objects")

        for doc in documents:
            # Ensure structure is correct
            if not isinstance(doc, Document):
                logger.info(f"Document type on issue: {type(doc)}")
                logger.error(f"Invalid document structure: {doc}")
                raise ValueError("Each document must be a LangChain Document object")
            else:
                logger.info(f"Document type: {type(doc)}")

            page_content = getattr(doc, "page_content", "").strip()
            metadata = getattr(doc, "metadata", {})

            # Validate fields
            if not page_content or not metadata:
                logger.info(f"Ingesting empty or invalid document: {doc}")
                logger.error("Invalid document: 'page_content' and 'metadata' must both be non-empty")
                raise ValueError("All documents must have non-empty 'page_content' and 'metadata'")

        # Final validation (extra safeguard)
        if not all(
            isinstance(doc, Document)
            and getattr(doc, "page_content", "").strip()
            and getattr(doc, "metadata", {})
            for doc in documents
        ):
            logger.error("Invalid documents: All must contain non-empty 'page_content' and 'metadata'")
            raise ValueError("All documents must contain non-empty 'page_content' and 'metadata'")

        logger.info(f"Ingesting {len(documents)} documents")
        try:
            self.vector_store.add(documents)
            logger.info("Document ingestion completed")
        except Exception as e:
            logger.error(f"Failed to ingest documents: {str(e)}")
            raise RuntimeError(f"Document ingestion failed: {str(e)}") from e
        
        
    def delete_documents(self, document_ids: List[str]) -> None:
        """
        Delete documents from the vector store.

        Args:
            document_ids (List[str]): A list of document IDs to be deleted.

        Raises:
            ValueError: If document_ids list is empty or contains invalid entries.
            RuntimeError: If document deletion fails.
        """
        if not document_ids or not isinstance(document_ids, list):
            logger.error("Invalid document_ids: Must provide a non-empty list of strings")
            raise ValueError("Document IDs must be a non-empty list of strings")
        
        if not all(isinstance(doc_id, str) and doc_id.strip() for doc_id in document_ids):
            logger.error("Invalid document_ids: All IDs must be non-empty strings")
            raise ValueError("All document IDs must be non-empty strings")

        logger.info(f"Deleting {len(document_ids)} documents with IDs: {document_ids}")
        try:
            self.vector_store.delete(document_ids)
            logger.info("Document deletion completed")
        except Exception as e:
            logger.error(f"Failed to delete documents with IDs {document_ids}: {str(e)}")
            raise RuntimeError(f"Document deletion failed: {str(e)}") from e

    def update_documents(self, documents: List[str]) -> None:
        """
        Update existing documents in the vector store.

        Args:
            documents (List[str]): A list of documents to be updated.

        Raises:
            ValueError: If documents list is empty or contains invalid entries.
            RuntimeError: If document update fails.
        """
        if not documents or not isinstance(documents, list):
            logger.error("Invalid documents: Must provide a non-empty list of strings")
            raise ValueError("Documents must be a non-empty list of strings")
        
        if not all(isinstance(doc, str) and doc.strip() for doc in documents):
            logger.error("Invalid documents: All documents must be non-empty strings")
            raise ValueError("All documents must be non-empty strings")

        logger.info(f"Updating {len(documents)} documents")
        try:
            self.vector_store.update(documents)
            logger.info("Document update completed")
        except Exception as e:
            logger.error(f"Failed to update documents: {str(e)}")
            raise RuntimeError(f"Document update failed: {str(e)}") from e

    def create_documents(self, text: str, source_url: str = "unknown") -> List[Document]:
        """
        Split text into documents using the text splitter, ensuring no empty strings.

        Args:
            text (str): Input text to be split.

        Returns:
            List[Document]: List of Document objects with non-empty content.

        Raises:
            ValueError: If text is empty or not a string, or if text_splitter is invalid.
            RuntimeError: If text splitting fails.
        """
        if not text or not isinstance(text, str):
            logger.error("Invalid text: Must provide a non-empty string")
            raise ValueError("Text must be a non-empty string")
        
        if not isinstance(self.text_splitter, RecursiveCharacterTextSplitter):
            logger.error("Invalid text_splitter: Must be an instance of RecursiveCharacterTextSplitter")
            raise ValueError("Text splitter must be a RecursiveCharacterTextSplitter")

        logger.info("Creating documents from text")
        try:
            texts = self.text_splitter.split_text(text)
            documents = [
                Document(page_content=chunk, metadata={"source": source_url})
                for chunk in texts if chunk.strip()
            ]
            if not documents:
                logger.warning("No non-empty documents created from text")
            else:
                logger.info(f"Created {len(documents)} non-empty documents")
            return documents
        except Exception as e:
            logger.error(f"Failed to create documents: {str(e)}")
            raise RuntimeError(f"Document creation failed: {str(e)}") from e

    def create_text_splitter(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> RecursiveCharacterTextSplitter:
        """
        Create a RecursiveCharacterTextSplitter.

        Args:
            chunk_size (int): Maximum size of each text chunk.
            chunk_overlap (int): Number of characters to overlap between chunks.

        Returns:
            RecursiveCharacterTextSplitter: Configured text splitter.

        Raises:
            ValueError: If chunk_size or chunk_overlap is invalid.
            RuntimeError: If text splitter creation fails.
        """
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            logger.error(f"Invalid chunk_size: {chunk_size}. Must be a positive integer")
            raise ValueError("Chunk size must be a positive integer")
        
        if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
            logger.error(f"Invalid chunk_overlap: {chunk_overlap}. Must be a non-negative integer")
            raise ValueError("Chunk overlap must be a non-negative integer")
        
        if chunk_overlap >= chunk_size:
            logger.error(f"Invalid chunk_overlap: {chunk_overlap}. Must be less than chunk_size ({chunk_size})")
            raise ValueError("Chunk overlap must be less than chunk size")

        logger.info(f"Creating text splitter with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                is_separator_regex=False,
            )
            logger.info("Text splitter created successfully")
            return text_splitter
        except Exception as e:
            logger.error(f"Failed to create text splitter: {str(e)}")
            raise RuntimeError(f"Text splitter creation failed: {str(e)}") from e
        

    def prepare_context(self, documents: List[Document]) -> str:
        """
        Prepare context from a list of documents.

        Args:
            documents (List[Document]): List of Document objects.

        Returns:
            tuple[str, dict]: Concatenated string of document contents and a map of {index: URL}.

        Raises:
            ValueError: If documents list is empty or contains invalid entries.
        """
        if not documents or not isinstance(documents, list):
            logger.error("Invalid documents: Must provide a non-empty list of Document objects")
            raise ValueError("Documents must be a non-empty list of Document objects")

        context = ""
        url_map = {}
        idx = 1
        for _doc in documents:
            doc, score = _doc
            if not isinstance(doc, Document):
                logger.error(f"Invalid document structure: {doc}")
                logger.info(f"Document type on issue on context preparing: {type(doc)}")
                continue
            source_url = doc.metadata.get("source", "unknown")
            if source_url != "unknown":
                url_map[str(idx)] = source_url
            
            context += f"Document [{idx}]:\n{doc.page_content}\n\n"
            idx += 1
        
        if not context:
            logger.warning("No valid content found in provided documents")
            return "No relevant documents found related this query.", {}

        logger.info(f"Prepared context with {len(context)} characters")
        return context, url_map
    