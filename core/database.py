"""Database operations using DuckDB."""
import os
import re
from collections import Counter
from typing import Optional
import duckdb
import pandas as pd
from .config import Config


class Database:
    """DuckDB database wrapper for analytics operations."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to DuckDB database file. If None, uses in-memory DB.
        """
        self.db_path = db_path or Config.DB_PATH
        self.con = None
        self._connect()
    
    def _connect(self):
        """Establish database connection."""
        # Create directory if needed
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.con = duckdb.connect(self.db_path)
    
    def close(self):
        """Close database connection."""
        if self.con:
            self.con.close()
            self.con = None
    
    def load_file(self, file_path: str, table_name: str = None) -> str:
        """
        Load CSV or Excel file into database table.
        
        Args:
            file_path: Path to CSV or Excel file
            table_name: Name for the table (defaults to filename without extension)
            
        Returns:
            The table name created
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        table_name = table_name or os.path.splitext(os.path.basename(file_path))[0]
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
        
        if ext == ".csv":
            self.con.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_csv_auto('{file_path}')
            """)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
            self.con.register("temp_df", df)
            self.con.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM temp_df
            """)
            self.con.unregister("temp_df")
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        return table_name
    
    def execute(self, query: str, params: tuple = None):
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Query results
        """
        if params:
            return self.con.execute(query, params)
        return self.con.execute(query)
    
    def fetch_all(self, query: str, params: tuple = None) -> list:
        """Execute query and fetch all results."""
        return self.execute(query, params).fetchall()
    
    def fetch_one(self, query: str, params: tuple = None):
        """Execute query and fetch one result."""
        return self.execute(query, params).fetchone()
    
    def fetch_df(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return as DataFrame."""
        return self.execute(query, params).fetchdf()
    
    def get_tables(self) -> list[str]:
        """Get list of all tables in database."""
        result = self.con.execute("SHOW TABLES").fetchall()
        return [r[0] for r in result]
    
    def get_schema(self, table: str) -> list[dict]:
        """
        Get schema for a table.
        
        Returns:
            List of dicts with 'column' and 'type' keys
        """
        rows = self.con.execute(f"DESCRIBE {table}").fetchall()
        return [{"column": r[0], "type": r[1]} for r in rows]
    
    def get_columns(self, table: str) -> list[str]:
        """Get list of column names for a table."""
        schema = self.get_schema(table)
        return [col["column"] for col in schema]
    
    def sample_column(self, table: str, column: str, limit: int = None) -> list[str]:
        """
        Get sample values from a column.
        
        Args:
            table: Table name
            column: Column name
            limit: Max number of samples
            
        Returns:
            List of sample values as strings
        """
        limit = limit or Config.SAMPLE_SIZE
        query = f'''
            SELECT "{column}"
            FROM {table}
            WHERE "{column}" IS NOT NULL
            LIMIT {limit}
        '''
        return [str(r[0]) for r in self.con.execute(query).fetchall()]
    
    def get_text_column_data(self, table: str, column: str, 
                             constraints: Optional[dict] = None) -> list[str]:
        """
        Get text data from a column with optional constraints.
        
        Args:
            table: Table name
            column: Column name (text column)
            constraints: Dict of column->value filters to apply
            
        Returns:
            List of text values
        """
        where_clauses = [f'"{column}" IS NOT NULL']
        
        if constraints:
            for col, val in constraints.items():
                if isinstance(val, str):
                    where_clauses.append(f'"{col}" = \'{val}\'')
                elif isinstance(val, (list, tuple)):
                    values = ", ".join([f"'{v}'" for v in val])
                    where_clauses.append(f'"{col}" IN ({values})')
                else:
                    where_clauses.append(f'"{col}" = {val}')
        
        where_sql = " AND ".join(where_clauses)
        query = f'SELECT "{column}" FROM {table} WHERE {where_sql}'
        
        rows = self.con.execute(query).fetchall()
        return [str(r[0]) for r in rows]
    
    def build_column_definitions(self, table: str) -> dict:
        """
        Build semantic column definitions for LLM prompt.
        
        Args:
            table: Table name
            
        Returns:
            Dict of column definitions with semantic types
        """
        schema = self.get_schema(table)
        definitions = {}
        
        for col in schema:
            name = col["column"]
            dtype = col["type"]
            samples = self.sample_column(table, name)
            semantic = self._infer_semantic(name, dtype, samples)
            
            definitions[name] = {
                "semantic_type": semantic,
                "duckdb_type": dtype,
                "sample_values": samples[:5]
            }
            
            # Extra metadata for categorical columns
            if semantic in {"categorical", "status_text"}:
                definitions[name]["allowed_values"] = list(
                    Counter(samples).keys()
                )[:10]
            
            # Range for numeric columns
            if semantic == "measure":
                nums = [float(v) for v in samples if self._is_numeric_string(v)]
                if nums:
                    definitions[name]["range"] = [min(nums), max(nums)]
        
        return definitions
    
    @staticmethod
    def _is_numeric_string(val: str) -> bool:
        """Check if string represents a number."""
        return bool(re.fullmatch(r"-?\d+(\.\d+)?", val.strip()))
    
    @staticmethod
    def _numeric_ratio(values: list) -> float:
        """Calculate ratio of numeric values in list."""
        if not values:
            return 0.0
        return sum(Database._is_numeric_string(v) for v in values) / len(values)
    
    @staticmethod
    def _unique_ratio(values: list) -> float:
        """Calculate ratio of unique values in list."""
        if not values:
            return 0.0
        return len(set(values)) / len(values)
    
    @staticmethod
    def _looks_like_datetime(values: list) -> bool:
        """Check if values look like datetime."""
        if not values:
            return False
        return all(any(ch.isdigit() for ch in v) for v in values)
    
    def _infer_semantic(self, column: str, dtype: str, samples: list) -> str:
        """Infer semantic type of a column."""
        joined = " ".join(samples).lower()
        u_ratio = self._unique_ratio(samples)
        n_ratio = self._numeric_ratio(samples)
        
        # Boolean
        if set(joined.split()).issubset({"yes", "no", "true", "false", "0", "1"}):
            return "boolean"
        
        # Identifier
        if u_ratio > 0.95 and ("int" in dtype.lower() or n_ratio > 0.9):
            return "identifier"
        
        # Numeric measure
        if "int" in dtype.lower() or "double" in dtype.lower() or "float" in dtype.lower():
            if u_ratio > 0.2:
                return "measure"
            else:
                return "countable"
        
        # Datetime
        if self._looks_like_datetime(samples):
            return "datetime"
        
        # Status-like text
        status_words = ["above", "below", "within", "pending", "completed",
                       "failed", "success", "open", "closed", "sla"]
        if any(word in joined for word in status_words):
            return "status_text"
        
        # Categorical
        if u_ratio < 0.2:
            return "categorical"
        
        # Free text
        return "free_text"


if __name__ == "__main__":
    db = Database(":memory:")
    print("Database initialized successfully")
