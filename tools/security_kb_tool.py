from typing import Dict, Any, ClassVar, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from rag_setup import SecurityKnowledgeBase

class SecurityQueryInput(BaseModel):
    """Input schema for security control queries"""
    query: str = Field(..., description="The security-related query to search for")
    n_results: int = Field(default=3, description="Number of relevant results to return")

class SecurityKnowledgeBaseTool(BaseTool):
    name: ClassVar[str] = "query_security_controls"
    description: ClassVar[str] = "Query the knowledge base for security controls and best practices"
    args_schema: ClassVar[Type[BaseModel]] = SecurityQueryInput
    
    # Use PrivateAttr for instance attributes that shouldn't be part of the model
    _kb: SecurityKnowledgeBase = PrivateAttr()
    
    def __init__(self):
        """Initialize the tool with a SecurityKnowledgeBase instance"""
        super().__init__()
        self._kb = SecurityKnowledgeBase()
        if self._kb.vector_store is None:
            self._kb.initialize_knowledge_base()
    
    def _run(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Run the tool to query security controls.
        
        Args:
            query: The security-related query to search for
            n_results: Number of relevant results to return
            
        Returns:
            Dictionary containing relevant security controls and their metadata
        """
        try:
            results = self._kb.query_knowledge_base(query, n_results)
            return {
                "query": query,
                "results": results,
                "total_results": len(results)
            }
        except Exception as e:
            return {
                "error": str(e),
                "results": []
            }

def init_security_tool() -> SecurityKnowledgeBaseTool:
    """Initialize and return the security knowledge base tool"""
    try:
        return SecurityKnowledgeBaseTool()
    except Exception as e:
        print(f"Error initializing security tool: {str(e)}")
        return None 