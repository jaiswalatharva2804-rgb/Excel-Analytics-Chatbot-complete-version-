"""Excel Analytics Chatbot - Main Application."""
import os
from typing import Optional, Dict, Any

from core import Database, Config
from handlers import (
    SQLHandler, ClusterHandler, RAGHandler,
    SchemaHandler, HybridHandler, TrendAnalyzer
)
from question_router import QuestionRouter


class ExcelAnalyticsChatbot:
    """
    Main chatbot class that orchestrates all components.
    
    Supports multiple question types:
    - SQL: Structured/numeric queries
    - CLUSTER: Text grouping/frequency analysis
    - RAG: Semantic/conceptual explanation
    - SCHEMA: Data structure/column questions
    - TREND: Time-based trend analysis
    - OVERVIEW: General insights
    - HYBRID: Complex questions requiring multiple approaches
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the chatbot.
        
        Args:
            db_path: Path to DuckDB database. Defaults to Config.DB_PATH
        """
        self.db = Database(db_path or Config.DB_PATH)
        self.table = None
        self.text_column = None
        self.router = None
        
        # Handlers (initialized lazily)
        self._sql_handler = None
        self._cluster_handler = None
        self._rag_handler = None
        self._schema_handler = None
        self._hybrid_handler = None
        self._trend_analyzer = None
    
    def load_data(self, file_path: str, table_name: str = None, 
                  text_column: str = None) -> str:
        """
        Load data from CSV or Excel file.
        
        Args:
            file_path: Path to CSV or Excel file
            table_name: Optional table name
            text_column: Name of text column for RAG/clustering
            
        Returns:
            Table name created
        """
        self.table = self.db.load_file(file_path, table_name)
        
        # Auto-detect text column if not provided
        if text_column:
            self.text_column = text_column
        else:
            self.text_column = self._detect_text_column()
        
        # Initialize router with column info
        columns = self.db.get_columns(self.table)
        self.router = QuestionRouter(columns)
        
        # Reset all handlers
        self._reset_handlers()
        
        return self.table
    
    def _reset_handlers(self):
        """Reset all handler instances."""
        self._sql_handler = None
        self._cluster_handler = None
        self._rag_handler = None
        self._schema_handler = None
        self._hybrid_handler = None
        self._trend_analyzer = None
    
    def use_existing_table(self, table_name: str, text_column: str = None):
        """
        Use an existing table in the database.
        
        Args:
            table_name: Name of existing table
            text_column: Name of text column for RAG/clustering
        """
        tables = self.db.get_tables()
        if table_name not in tables:
            raise ValueError(f"Table '{table_name}' not found. Available: {tables}")
        
        self.table = table_name
        self.text_column = text_column or self._detect_text_column()
        
        columns = self.db.get_columns(self.table)
        self.router = QuestionRouter(columns)
        
        # Reset all handlers
        self._reset_handlers()
    
    def _detect_text_column(self) -> Optional[str]:
        """Auto-detect the main text column."""
        if not self.table:
            return None
        
        columns = self.db.get_columns(self.table)
        definitions = self.db.build_column_definitions(self.table)
        
        # Look for free_text columns
        for col in columns:
            if definitions.get(col, {}).get("semantic_type") == "free_text":
                return col
        
        # Fallback: look for common names
        text_names = ["review", "feedback", "comment", "description", "text", 
                     "notes", "reason", "issue", "complaint", "message"]
        for col in columns:
            if col.lower() in text_names:
                return col
        
        return None
    
    @property
    def sql_handler(self) -> SQLHandler:
        """Lazily initialize SQL handler."""
        if self._sql_handler is None:
            if not self.table:
                raise ValueError("No table loaded. Call load_data() first.")
            self._sql_handler = SQLHandler(self.db, self.table)
        return self._sql_handler
    
    @property
    def cluster_handler(self) -> ClusterHandler:
        """Lazily initialize cluster handler."""
        if self._cluster_handler is None:
            if not self.table or not self.text_column:
                raise ValueError("No table/text column. Call load_data() first.")
            self._cluster_handler = ClusterHandler(
                self.db, self.table, self.text_column
            )
        return self._cluster_handler
    
    @property
    def rag_handler(self) -> RAGHandler:
        """Lazily initialize RAG handler."""
        if self._rag_handler is None:
            if not self.table or not self.text_column:
                raise ValueError("No table/text column. Call load_data() first.")
            self._rag_handler = RAGHandler(
                self.db, self.table, self.text_column
            )
        return self._rag_handler
    
    @property
    def schema_handler(self) -> SchemaHandler:
        """Lazily initialize schema handler."""
        if self._schema_handler is None:
            if not self.table:
                raise ValueError("No table loaded. Call load_data() first.")
            self._schema_handler = SchemaHandler(self.db, self.table)
        return self._schema_handler
    
    @property
    def hybrid_handler(self) -> HybridHandler:
        """Lazily initialize hybrid handler."""
        if self._hybrid_handler is None:
            if not self.table:
                raise ValueError("No table loaded. Call load_data() first.")
            self._hybrid_handler = HybridHandler(
                self.db, self.table, self.text_column
            )
        return self._hybrid_handler
    
    @property
    def trend_analyzer(self) -> TrendAnalyzer:
        """Lazily initialize trend analyzer."""
        if self._trend_analyzer is None:
            if not self.table:
                raise ValueError("No table loaded. Call load_data() first.")
            self._trend_analyzer = TrendAnalyzer(self.db, self.table)
        return self._trend_analyzer
    
    def ask(self, question: str, constraints: Optional[dict] = None) -> str:
        """
        Ask a question and get an answer.
        
        Args:
            question: Natural language question
            constraints: Optional explicit constraints to apply
            
        Returns:
            Natural language answer
        """
        if not self.table:
            return "No data loaded. Please load a file first using load_data()."
        
        if not self.router:
            columns = self.db.get_columns(self.table)
            self.router = QuestionRouter(columns)
        
        # Route the question
        routing = self.router.route(question)
        route = routing["route"]
        
        # Merge constraints
        extracted_constraints = routing.get("constraints")
        if constraints:
            if extracted_constraints:
                extracted_constraints.update(constraints)
            else:
                extracted_constraints = constraints
        
        # Handle based on route
        try:
            if route == QuestionRouter.SCHEMA:
                return self.schema_handler.handle(question, extracted_constraints)
            
            elif route == QuestionRouter.SQL:
                return self.sql_handler.handle(question, extracted_constraints)
            
            elif route == QuestionRouter.CLUSTER:
                if not self.text_column:
                    return "No text column available for clustering analysis. Using hybrid analysis instead."
                return self.cluster_handler.handle(question, extracted_constraints)
            
            elif route == QuestionRouter.RAG:
                if not self.text_column:
                    # Fall back to hybrid if no text column
                    return self.hybrid_handler.handle(question, extracted_constraints)
                return self.rag_handler.handle(question, extracted_constraints)
            
            elif route == QuestionRouter.TREND:
                return self.trend_analyzer.analyze_trend(question)
            
            elif route == QuestionRouter.OVERVIEW:
                return self.hybrid_handler.general_overview()
            
            elif route == QuestionRouter.HYBRID:
                return self.hybrid_handler.handle(question, extracted_constraints)
            
            else:
                # Unknown route - default to hybrid
                return self.hybrid_handler.handle(question, extracted_constraints)
                
        except Exception as e:
            return f"Error processing question: {str(e)}\n\nPlease try rephrasing your question."
    
    def get_schema(self) -> dict:
        """Get schema information for the current table."""
        if not self.table:
            return {}
        return self.db.build_column_definitions(self.table)
    
    def close(self):
        """Close database connection."""
        self.db.close()


def print_help():
    """Print help message."""
    print("""
📊 Excel Analytics Chatbot - Commands
=====================================

FILE COMMANDS:
  load <path>      Load a CSV or Excel file
  tables           List loaded tables
  
INFO COMMANDS:
  help             Show this help message
  schema           Show column details (quick view)
  columns          Explain all columns in detail
  
EXAMPLE QUESTIONS:
  • "What columns are available?"           → Schema info
  • "Explain all the columns"               → Detailed column descriptions
  • "How many records are there?"           → SQL query
  • "What is the average rating?"           → SQL aggregation
  • "Top 10 by score"                       → SQL ranking
  • "What are the most common complaints?"  → Clustering analysis
  • "Why are customers unhappy?"            → RAG analysis
  • "Show the trend over time"              → Trend analysis
  • "Give me an overview of the data"       → General insights
  • "Analyze the discount patterns"         → Hybrid analysis

OTHER:
  quit / exit      Exit the chatbot
""")


def main():
    """Interactive chatbot loop."""
    print("=" * 55)
    print("  📊 Excel Analytics Chatbot (Local LLM Powered)")
    print("=" * 55)
    
    chatbot = ExcelAnalyticsChatbot()
    
    # Check for sample data
    sample_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "excel_sample", "clean_unique_reviews_1000_rows.csv"
    )
    
    if os.path.exists(sample_path):
        print(f"\n📁 Loading sample data...")
        try:
            chatbot.load_data(sample_path)
            print(f"✓ Loaded table: {chatbot.table}")
            print(f"✓ Text column: {chatbot.text_column}")
            print(f"✓ Total columns: {len(chatbot.db.get_columns(chatbot.table))}")
        except Exception as e:
            print(f"✗ Error loading sample: {e}")
    else:
        print("\n⚠️  No sample data found.")
        print("   Use 'load <path>' to load a CSV or Excel file.")
    
    print("\n💡 Type 'help' for commands, 'quit' to exit")
    print("-" * 55)
    
    while True:
        try:
            question = input("\n🧑 You: ").strip()
            
            if not question:
                continue
            
            question_lower = question.lower()
            
            # Exit commands
            if question_lower in ["quit", "exit", "q"]:
                break
            
            # Help command
            if question_lower == "help":
                print_help()
                continue
            
            # Schema quick view
            if question_lower == "schema":
                if not chatbot.table:
                    print("No data loaded. Use 'load <path>' first.")
                    continue
                schema = chatbot.get_schema()
                print(f"\n📊 Table: {chatbot.table}")
                print(f"   Columns: {len(schema)}")
                print("-" * 40)
                for col, info in schema.items():
                    sem_type = info.get('semantic_type', 'unknown')
                    dtype = info.get('duckdb_type', 'unknown')
                    print(f"  • {col}: {sem_type} ({dtype})")
                continue
            
            # List tables
            if question_lower == "tables":
                tables = chatbot.db.get_tables()
                if tables:
                    print(f"\n📋 Available tables: {', '.join(tables)}")
                else:
                    print("\n⚠️  No tables loaded.")
                continue
            
            # Load file command
            if question_lower.startswith("load "):
                path = question[5:].strip().strip('"').strip("'")
                if not path:
                    print("Usage: load <file_path>")
                    continue
                try:
                    print(f"\n📁 Loading {path}...")
                    chatbot.load_data(path)
                    print(f"✓ Loaded table: {chatbot.table}")
                    print(f"✓ Columns: {len(chatbot.db.get_columns(chatbot.table))}")
                    if chatbot.text_column:
                        print(f"✓ Text column: {chatbot.text_column}")
                except FileNotFoundError:
                    print(f"✗ File not found: {path}")
                except Exception as e:
                    print(f"✗ Error loading file: {e}")
                continue
            
            # Columns detailed view (shortcut)
            if question_lower in ["columns", "cols"]:
                question = "explain all columns"
            
            # Ask the question
            if not chatbot.table:
                print("\n⚠️  No data loaded. Use 'load <path>' first.")
                continue
            
            print("\n🤖 Bot: Thinking...")
            response = chatbot.ask(question)
            print(f"\n🤖 Bot:\n{response}")
            
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    chatbot.close()
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
