"""
Chatbot API - Clean interface for web/app integration.

This module provides a JSON-based API that can be easily integrated
with web frameworks (Flask, FastAPI) or desktop applications.

Usage:
    from api import ChatbotAPI
    
    # Initialize
    api = ChatbotAPI()
    
    # Load data
    result = api.load_file("path/to/data.csv")
    
    # Ask questions
    response = api.ask("What columns are available?")
    
    # Get schema
    schema = api.get_schema()
"""
import os
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import ExcelAnalyticsChatbot


@dataclass
class APIResponse:
    """Standardized API response format."""
    success: bool
    data: Any = None
    error: str = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SessionInfo:
    """Information about a chatbot session."""
    session_id: str
    table_name: str = None
    text_column: str = None
    columns: List[str] = None
    row_count: int = 0
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class ChatbotAPI:
    """
    Clean API layer for the Excel Analytics Chatbot.
    
    Designed for easy integration with:
    - Flask / FastAPI web frameworks
    - Desktop GUI applications
    - REST API endpoints
    - WebSocket connections
    
    All methods return standardized APIResponse objects.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the API.
        
        Args:
            db_path: Optional path to DuckDB database
        """
        self._chatbot = ExcelAnalyticsChatbot(db_path)
        self._session_id = str(uuid.uuid4())
        self._history: List[Dict] = []
    
    @property
    def session_id(self) -> str:
        """Get current session ID."""
        return self._session_id
    
    @property
    def is_data_loaded(self) -> bool:
        """Check if data has been loaded."""
        return self._chatbot.table is not None
    
    def get_session_info(self) -> APIResponse:
        """
        Get information about the current session.
        
        Returns:
            APIResponse with SessionInfo data
        """
        try:
            info = SessionInfo(
                session_id=self._session_id,
                table_name=self._chatbot.table,
                text_column=self._chatbot.text_column,
                columns=self._chatbot.db.get_columns(self._chatbot.table) if self._chatbot.table else [],
                row_count=self._get_row_count()
            )
            return APIResponse(success=True, data=info.to_dict() if hasattr(info, 'to_dict') else asdict(info))
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def _get_row_count(self) -> int:
        """Get row count for current table."""
        if not self._chatbot.table:
            return 0
        try:
            result = self._chatbot.db.fetch_one(
                f'SELECT COUNT(*) FROM {self._chatbot.table}'
            )
            return result[0] if result else 0
        except Exception:
            return 0
    
    def load_file(self, file_path: str, table_name: str = None, 
                  text_column: str = None) -> APIResponse:
        """
        Load a CSV or Excel file.
        
        Args:
            file_path: Path to CSV or Excel file
            table_name: Optional custom table name
            text_column: Optional text column for RAG analysis
            
        Returns:
            APIResponse with load result
        """
        try:
            if not os.path.exists(file_path):
                return APIResponse(
                    success=False, 
                    error=f"File not found: {file_path}"
                )
            
            table = self._chatbot.load_data(file_path, table_name, text_column)
            
            return APIResponse(
                success=True,
                data={
                    "table_name": table,
                    "text_column": self._chatbot.text_column,
                    "columns": self._chatbot.db.get_columns(table),
                    "row_count": self._get_row_count()
                }
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def ask(self, question: str, constraints: Dict = None, 
            include_routing: bool = False) -> APIResponse:
        """
        Ask a question and get an answer.
        
        Args:
            question: Natural language question
            constraints: Optional filters to apply
            include_routing: Whether to include routing info in response
            
        Returns:
            APIResponse with answer
        """
        if not self.is_data_loaded:
            return APIResponse(
                success=False,
                error="No data loaded. Please load a file first."
            )
        
        try:
            # Get routing info if requested
            routing_info = None
            if include_routing:
                routing_info = self._chatbot.router.route(question)
            
            # Get answer
            answer = self._chatbot.ask(question, constraints)
            
            # Record in history
            self._history.append({
                "question": question,
                "answer": answer[:500] + "..." if len(answer) > 500 else answer,
                "timestamp": datetime.utcnow().isoformat(),
                "route": routing_info["route"] if routing_info else None
            })
            
            response_data = {
                "answer": answer,
                "question": question
            }
            
            if include_routing:
                response_data["routing"] = routing_info
            
            return APIResponse(success=True, data=response_data)
            
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def get_schema(self, detailed: bool = False) -> APIResponse:
        """
        Get schema information for the loaded data.
        
        Args:
            detailed: Whether to include detailed column profiles
            
        Returns:
            APIResponse with schema data
        """
        if not self.is_data_loaded:
            return APIResponse(
                success=False,
                error="No data loaded."
            )
        
        try:
            schema = self._chatbot.get_schema()
            
            if detailed:
                # Add more details
                columns_info = []
                for col, info in schema.items():
                    columns_info.append({
                        "name": col,
                        "type": info.get("duckdb_type"),
                        "semantic_type": info.get("semantic_type"),
                        "sample_values": info.get("sample_values", [])[:5],
                        "allowed_values": info.get("allowed_values"),
                        "range": info.get("range")
                    })
                return APIResponse(success=True, data={"columns": columns_info})
            
            return APIResponse(success=True, data=schema)
            
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def explain_columns(self) -> APIResponse:
        """
        Get detailed explanation of all columns.
        
        Returns:
            APIResponse with column explanations
        """
        return self.ask("explain all columns", include_routing=False)
    
    def get_overview(self) -> APIResponse:
        """
        Get general overview/insights about the data.
        
        Returns:
            APIResponse with overview
        """
        return self.ask("give me an overview of the data", include_routing=False)
    
    def get_tables(self) -> APIResponse:
        """
        Get list of available tables.
        
        Returns:
            APIResponse with table list
        """
        try:
            tables = self._chatbot.db.get_tables()
            return APIResponse(success=True, data={"tables": tables})
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def use_table(self, table_name: str, text_column: str = None) -> APIResponse:
        """
        Switch to using an existing table.
        
        Args:
            table_name: Name of table to use
            text_column: Optional text column name
            
        Returns:
            APIResponse with result
        """
        try:
            self._chatbot.use_existing_table(table_name, text_column)
            return APIResponse(
                success=True,
                data={
                    "table_name": table_name,
                    "text_column": self._chatbot.text_column,
                    "columns": self._chatbot.db.get_columns(table_name)
                }
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def get_history(self, limit: int = 10) -> APIResponse:
        """
        Get conversation history.
        
        Args:
            limit: Max number of items to return
            
        Returns:
            APIResponse with history
        """
        return APIResponse(
            success=True,
            data={"history": self._history[-limit:]}
        )
    
    def clear_history(self) -> APIResponse:
        """Clear conversation history."""
        self._history = []
        return APIResponse(success=True, data={"message": "History cleared"})
    
    def execute_sql(self, query: str) -> APIResponse:
        """
        Execute a raw SQL query (use with caution).
        
        Args:
            query: SQL query to execute
            
        Returns:
            APIResponse with query results
        """
        if not self.is_data_loaded:
            return APIResponse(success=False, error="No data loaded.")
        
        try:
            # Only allow SELECT queries for safety
            if not query.strip().upper().startswith("SELECT"):
                return APIResponse(
                    success=False,
                    error="Only SELECT queries are allowed"
                )
            
            results = self._chatbot.db.fetch_all(query)
            return APIResponse(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "row_count": len(results)
                }
            )
        except Exception as e:
            return APIResponse(success=False, error=str(e))
    
    def close(self):
        """Close the API and release resources."""
        try:
            self._chatbot.close()
        except Exception:
            pass


# Convenience function for quick setup
def create_api(file_path: str = None, db_path: str = None) -> ChatbotAPI:
    """
    Create and optionally initialize a ChatbotAPI instance.
    
    Args:
        file_path: Optional path to load data from
        db_path: Optional database path
        
    Returns:
        Initialized ChatbotAPI instance
    """
    api = ChatbotAPI(db_path)
    
    if file_path:
        result = api.load_file(file_path)
        if not result.success:
            raise ValueError(f"Failed to load file: {result.error}")
    
    return api


if __name__ == "__main__":
    # Demo usage
    print("ChatbotAPI Demo")
    print("=" * 40)
    
    api = ChatbotAPI()
    
    # Show session info
    session = api.get_session_info()
    print(f"Session ID: {session.data['session_id']}")
    
    # Try to load sample data
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "excel_sample", "clean_unique_reviews_1000_rows.csv"
    )
    
    if os.path.exists(sample_path):
        print(f"\nLoading: {sample_path}")
        result = api.load_file(sample_path)
        
        if result.success:
            print(f"✓ Loaded table: {result.data['table_name']}")
            print(f"✓ Columns: {len(result.data['columns'])}")
            
            # Get schema
            schema = api.get_schema()
            print(f"\nSchema: {list(schema.data.keys())[:5]}...")
            
            # Ask a question
            print("\nAsking: 'What columns are available?'")
            answer = api.ask("What columns are available?", include_routing=True)
            print(f"Route: {answer.data.get('routing', {}).get('route', 'N/A')}")
            print(f"Answer preview: {answer.data['answer'][:200]}...")
        else:
            print(f"✗ Error: {result.error}")
    else:
        print(f"Sample file not found: {sample_path}")
    
    api.close()
    print("\n✓ Demo complete")
