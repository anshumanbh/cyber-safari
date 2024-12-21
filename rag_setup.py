from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import MarkdownTextSplitter
from langchain_core.documents import Document
import os
from pathlib import Path
import json

class SecurityKnowledgeBase:
    def __init__(self, 
                 docs_directory: str = "./security_docs",
                 persist_directory: str = "./security_kb"):
        """Initialize the security knowledge base"""
        self.docs_directory = Path(docs_directory)
        self.persist_directory = Path(persist_directory)
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = MarkdownTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        # Initialize or load existing vector store
        if self.persist_directory.exists():
            self.vector_store = Chroma(
                persist_directory=str(self.persist_directory),
                embedding_function=self.embeddings
            )
        else:
            self.vector_store = None
    
    def load_markdown_file(self, file_path: Path) -> List[Document]:
        """Load and process a single markdown file"""
        # Read the markdown content
        content = file_path.read_text()
        
        # Extract metadata from the file path
        category = file_path.parent.name
        
        metadata = {
            "title": file_path.stem,
            "category": category,
            "source_file": str(file_path)
        }
        
        # Split content into chunks
        texts = self.text_splitter.split_text(content)
        
        # Create documents
        docs = []
        for i, text in enumerate(texts):
            doc_metadata = {
                "chunk_id": i,
                **metadata
            }
            docs.append(Document(page_content=text, metadata=doc_metadata))
        
        return docs
    
    def initialize_knowledge_base(self):
        """Initialize the vector store with all markdown files in docs directory"""
        if not self.docs_directory.exists():
            raise ValueError(f"Documents directory {self.docs_directory} does not exist")
        
        all_docs = []
        
        # Recursively find all .md files
        for md_file in self.docs_directory.rglob("*.md"):
            docs = self.load_markdown_file(md_file)
            all_docs.extend(docs)
            print(f"Processed {md_file.name}")
        
        if not all_docs:
            raise ValueError("No markdown files found in documents directory")
        
        # Create new vector store
        self.vector_store = Chroma.from_documents(
            documents=all_docs,
            embedding=self.embeddings,
            persist_directory=str(self.persist_directory)
        )
        self.vector_store.persist()
        
        print(f"Initialized knowledge base with {len(all_docs)} documents")
    
    def query_knowledge_base(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant security controls"""
        if not self.vector_store:
            raise ValueError("Knowledge base not initialized")
        
        # Get relevant documents
        docs = self.vector_store.similarity_search_with_relevance_scores(
            query, k=n_results
        )
        
        # Format results
        results = []
        for doc, score in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": score
            })
        
        return results

def setup_knowledge_base():
    """Set up and test the security knowledge base"""
    # Create test queries
    test_queries = [
        "How to implement JWT authentication?",
        # "What are the best practices for admin endpoint security?",
        # "How to secure API endpoints using headers?"
    ]
    
    try:
        # Initialize knowledge base
        kb = SecurityKnowledgeBase()
        kb.initialize_knowledge_base()
        
        # Test queries
        print("\nTesting knowledge base queries:")
        for query in test_queries:
            print(f"\nQuery: {query}")
            results = kb.query_knowledge_base(query, n_results=1)
            for result in results:
                print(f"\nRelevance Score: {result['relevance_score']:.2f}")
                print(f"Category: {result['metadata']['category']}")
                print(f"Source: {result['metadata']['source_file']}")
                print(f"Content Preview: {result['content'][:200]}...")
        
        return kb
        
    except Exception as e:
        print(f"Error setting up knowledge base: {str(e)}")
        return None

if __name__ == "__main__":
    kb = setup_knowledge_base()