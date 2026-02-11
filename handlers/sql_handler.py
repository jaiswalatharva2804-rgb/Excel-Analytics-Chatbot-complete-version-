"""SQL Handler for structured/numeric queries."""
from typing import Optional
from core import call_llm, Database


class SQLHandler:
    """Handles SQL-based queries for structured/numeric data."""
    
    def __init__(self, db: Database, table: str):
        """
        Initialize SQL handler.
        
        Args:
            db: Database instance
            table: Table name to query
        """
        self.db = db
        self.table = table
        self._column_definitions = None
    
    @property
    def column_definitions(self) -> dict:
        """Lazily build column definitions."""
        if self._column_definitions is None:
            self._column_definitions = self.db.build_column_definitions(self.table)
        return self._column_definitions
    
    def _format_schema_prompt(self) -> str:
        """Format column definitions for LLM prompt."""
        lines = [f"table name:\n{self.table}", "columns and their types and semantic meanings:"]
        
        for col, meta in self.column_definitions.items():
            lines.append(f"\n{col}:")
            for key, value in meta.items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    def generate_sql(self, question: str, constraints: Optional[dict] = None) -> str:
        """
        Generate SQL query from natural language question.
        
        Args:
            question: Natural language question
            constraints: Optional dict of column->value filters
            
        Returns:
            Generated SQL query or error message
        """
        schema_info = self._format_schema_prompt()
        
        # Add constraint info to prompt if provided
        constraint_text = ""
        if constraints:
            constraint_parts = [f"- {col} = '{val}'" for col, val in constraints.items()]
            constraint_text = f"""
ADDITIONAL CONSTRAINTS (MUST be included in WHERE clause):
{chr(10).join(constraint_parts)}
"""
        
        prompt = f"""
You are an expert SQL query generator specialized in DuckDB/SQLite.

Your task is to convert the user's natural language request into a valid SQL query
using ONLY the provided table schema and column names.

INTERPRETATION GUIDELINES:
- Map user terms to the closest matching column:
  * "session length", "call length", "duration" → look for duration/time columns
  * "score", "rating" → look for score/rating columns
  * "top 10", "highest" → ORDER BY DESC LIMIT 10
  * "bottom 10", "lowest" → ORDER BY ASC LIMIT 10

STRICT RULES:
1. Use ONLY column names exactly as provided in the schema.
2. Do NOT rename columns - use them exactly as shown.
3. ALWAYS wrap column names in double quotes, especially if they contain spaces.
   Example: "Call Duration (Minutes)" NOT Call Duration (Minutes)
4. The output must be valid DuckDB SQL (use LIMIT, not TOP).

{constraint_text}

OUTPUT RULES:
- If the request can be answered → output ONLY the SQL query.
- If truly impossible → output: "I'm sorry — this request cannot be answered using the available data."
- No explanations. No markdown.

{schema_info}

Request:
"{question}"
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Return only valid SQL. No explanation.",
            temperature=0.0
        )
    
    def execute_sql(self, sql: str):
        """
        Execute SQL and return results.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Query results
        """
        return self.db.fetch_all(sql)
    
    def format_response(self, question: str, sql: str, results, 
                        schema_context: dict = None) -> str:
        """
        Use LLM to format SQL results with comprehensive insights.
        
        Args:
            question: Original question
            sql: SQL query executed
            results: Query results
            schema_context: Column metadata for better interpretation
            
        Returns:
            Natural language response with insights
        """
        # Build context about the data
        result_count = len(results) if isinstance(results, list) else 1
        
        # Extract numeric values for statistical context
        numeric_context = ""
        if results and isinstance(results, list) and len(results) > 0:
            # Try to identify numeric columns in results
            try:
                numeric_vals = []
                for row in results:
                    for val in row:
                        if isinstance(val, (int, float)):
                            numeric_vals.append(val)
                if numeric_vals:
                    avg_val = sum(numeric_vals) / len(numeric_vals)
                    min_val = min(numeric_vals)
                    max_val = max(numeric_vals)
                    numeric_context = f"""
Statistical Context:
- Count: {len(numeric_vals)} values
- Range: {min_val} to {max_val}
- Average: {avg_val:.2f}
"""
            except:
                pass
        
        prompt = f"""
You are an expert data analyst providing insights on query results.

User Question: "{question}"

SQL Query: {sql}

Results ({result_count} rows):
{results}
{numeric_context}

Provide a comprehensive response:

1. **Answer**: Direct answer to the question with specific numbers

2. **Data Summary**: 
   - Present key figures clearly
   - Use tables or lists for multiple results
   - Highlight notable values (highest, lowest, outliers)

3. **Insights & Analysis**:
   - What patterns do you observe?
   - Are there any notable trends or anomalies?
   - What might these numbers indicate?
   - Compare values where relevant (e.g., "X is 30% higher than Y")

4. **Business Implications** (if applicable):
   - What could this data suggest for decision-making?
   - Any recommendations based on the numbers?

Be specific, use actual values, and make the analysis actionable.
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Provide insightful, data-driven analysis with specific numbers and actionable insights.",
            temperature=0.2
        )
    
    def handle(self, question: str, constraints: Optional[dict] = None) -> str:
        """
        Full pipeline: question -> SQL -> execute -> response.
        
        Args:
            question: Natural language question
            constraints: Optional filters to apply
            
        Returns:
            Natural language response
        """
        # Generate SQL
        sql = self.generate_sql(question, constraints)
        
        # Check if SQL generation failed
        if sql.startswith("I'm sorry"):
            return sql
        
        try:
            # Execute SQL
            results = self.execute_sql(sql)
            
            # Format response
            return self.format_response(question, sql, results)
            
        except Exception as e:
            return f"Error executing query: {str(e)}\nGenerated SQL: {sql}"


if __name__ == "__main__":
    # Test
    db = Database(":memory:")
    handler = SQLHandler(db, "test")
    print("SQLHandler initialized")
