"""Data Profiler - Comprehensive column analysis and data overview."""
from typing import Optional
import numpy as np
from collections import Counter

from core import call_llm, Database, Config


class DataProfiler:
    """Profiles data to understand columns, types, and generate descriptions."""
    
    def __init__(self, db: Database, table: str):
        """
        Initialize profiler.
        
        Args:
            db: Database instance
            table: Table name to profile
        """
        self.db = db
        self.table = table
        self._profile_cache = None
    
    def profile_column(self, column: str) -> dict:
        """
        Generate comprehensive profile for a single column.
        
        Returns:
            Dict with column statistics and metadata
        """
        # Get basic info
        schema = self.db.get_schema(self.table)
        col_info = next((c for c in schema if c["column"] == column), None)
        
        if not col_info:
            raise ValueError(f"Column '{column}' not found")
        
        dtype = col_info["type"]
        
        # Get sample values
        samples = self.db.sample_column(self.table, column, limit=100)
        
        # Count stats
        total_query = f'SELECT COUNT(*) FROM {self.table}'
        null_query = f'SELECT COUNT(*) FROM {self.table} WHERE "{column}" IS NULL'
        distinct_query = f'SELECT COUNT(DISTINCT "{column}") FROM {self.table}'
        
        total_count = self.db.fetch_one(total_query)[0]
        null_count = self.db.fetch_one(null_query)[0]
        distinct_count = self.db.fetch_one(distinct_query)[0]
        
        profile = {
            "column_name": column,
            "data_type": dtype,
            "total_rows": total_count,
            "null_count": null_count,
            "null_percentage": round(null_count / total_count * 100, 1) if total_count > 0 else 0,
            "distinct_count": distinct_count,
            "unique_percentage": round(distinct_count / total_count * 100, 1) if total_count > 0 else 0,
            "sample_values": samples[:10]
        }
        
        # Add numeric stats if applicable
        if "int" in dtype.lower() or "double" in dtype.lower() or "float" in dtype.lower():
            try:
                stats_query = f'''
                    SELECT 
                        MIN("{column}"), 
                        MAX("{column}"), 
                        AVG("{column}"),
                        MEDIAN("{column}")
                    FROM {self.table}
                    WHERE "{column}" IS NOT NULL
                '''
                stats = self.db.fetch_one(stats_query)
                profile["numeric_stats"] = {
                    "min": stats[0],
                    "max": stats[1],
                    "mean": round(stats[2], 2) if stats[2] else None,
                    "median": stats[3]
                }
            except:
                pass
        
        # Add categorical stats if low cardinality
        if distinct_count <= 20 and distinct_count > 0:
            try:
                freq_query = f'''
                    SELECT "{column}", COUNT(*) as cnt 
                    FROM {self.table} 
                    WHERE "{column}" IS NOT NULL
                    GROUP BY "{column}" 
                    ORDER BY cnt DESC 
                    LIMIT 10
                '''
                freq = self.db.fetch_all(freq_query)
                profile["value_distribution"] = {str(row[0]): row[1] for row in freq}
            except:
                pass
        
        # Check for date patterns
        if samples:
            date_indicators = ["-", "/", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]
            if any(ind in str(samples[0]) for ind in date_indicators):
                profile["likely_date"] = True
        
        return profile
    
    def profile_all_columns(self) -> dict:
        """
        Profile all columns in the table.
        
        Returns:
            Dict mapping column names to their profiles
        """
        if self._profile_cache:
            return self._profile_cache
        
        columns = self.db.get_columns(self.table)
        profiles = {}
        
        for col in columns:
            try:
                profiles[col] = self.profile_column(col)
            except Exception as e:
                profiles[col] = {"error": str(e)}
        
        self._profile_cache = profiles
        return profiles
    
    def get_data_overview(self) -> dict:
        """
        Get high-level overview of the entire dataset.
        
        Returns:
            Dict with dataset statistics
        """
        columns = self.db.get_columns(self.table)
        
        # Row count
        row_count = self.db.fetch_one(f'SELECT COUNT(*) FROM {self.table}')[0]
        
        # Identify column types
        profiles = self.profile_all_columns()
        
        numeric_cols = []
        categorical_cols = []
        text_cols = []
        date_cols = []
        
        for col, profile in profiles.items():
            if "error" in profile:
                continue
            dtype = profile.get("data_type", "").lower()
            distinct_pct = profile.get("unique_percentage", 0)
            
            if "int" in dtype or "double" in dtype or "float" in dtype:
                numeric_cols.append(col)
            elif "date" in dtype or "time" in dtype or profile.get("likely_date"):
                date_cols.append(col)
            elif distinct_pct < 10:
                categorical_cols.append(col)
            else:
                text_cols.append(col)
        
        return {
            "table_name": self.table,
            "row_count": row_count,
            "column_count": len(columns),
            "columns": columns,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "text_columns": text_cols,
            "date_columns": date_cols
        }
    
    def generate_column_descriptions(self) -> str:
        """
        Use LLM to generate human-readable descriptions for all columns.
        
        Returns:
            Formatted string with column descriptions
        """
        profiles = self.profile_all_columns()
        overview = self.get_data_overview()
        
        # Build context for LLM
        column_info = []
        for col, profile in profiles.items():
            if "error" in profile:
                continue
            
            info = f"Column: {col}\n"
            info += f"  Type: {profile.get('data_type')}\n"
            info += f"  Unique values: {profile.get('distinct_count')} ({profile.get('unique_percentage')}%)\n"
            info += f"  Null values: {profile.get('null_count')} ({profile.get('null_percentage')}%)\n"
            info += f"  Samples: {profile.get('sample_values', [])[:5]}\n"
            
            if "numeric_stats" in profile:
                stats = profile["numeric_stats"]
                info += f"  Range: {stats['min']} to {stats['max']}, Mean: {stats['mean']}\n"
            
            if "value_distribution" in profile:
                top_vals = list(profile["value_distribution"].items())[:5]
                info += f"  Top values: {top_vals}\n"
            
            column_info.append(info)
        
        prompt = f"""
You are a data analyst explaining a dataset to a business user.

Dataset Overview:
- Table: {overview['table_name']}
- Total rows: {overview['row_count']}
- Total columns: {overview['column_count']}

Column Details:
{chr(10).join(column_info)}

Generate a clear, business-friendly description for each column:
1. What the column likely represents
2. The type of data it contains
3. Notable characteristics (if any)

Format as a structured list. Be concise but informative.
Base descriptions ONLY on the actual data shown - do not assume or invent meanings.
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Describe data columns based only on the evidence provided.",
            temperature=0.1
        )
    
    def answer_schema_question(self, question: str) -> str:
        """
        Answer questions about the data schema/structure.
        
        Args:
            question: User's question about columns/structure
            
        Returns:
            Answer based on actual data profile
        """
        profiles = self.profile_all_columns()
        overview = self.get_data_overview()
        
        # Build detailed context
        context = f"""
Dataset: {overview['table_name']}
Total Rows: {overview['row_count']}
Total Columns: {overview['column_count']}

Columns Overview:
"""
        for col, profile in profiles.items():
            if "error" in profile:
                context += f"\n{col}: [Error reading column]\n"
                continue
            
            context += f"\n{col}:\n"
            context += f"  - Type: {profile.get('data_type')}\n"
            context += f"  - Distinct values: {profile.get('distinct_count')}\n"
            context += f"  - Nulls: {profile.get('null_percentage')}%\n"
            context += f"  - Samples: {profile.get('sample_values', [])[:3]}\n"
            
            if "numeric_stats" in profile:
                stats = profile["numeric_stats"]
                context += f"  - Stats: min={stats['min']}, max={stats['max']}, mean={stats['mean']}\n"
            
            if "value_distribution" in profile:
                context += f"  - Categories: {list(profile['value_distribution'].keys())[:5]}\n"
        
        prompt = f"""
You are a data expert answering questions about a dataset's structure.

{context}

Question: {question}

Answer the question using ONLY the information provided above.
Be specific and cite actual column names, values, and statistics.
If the question cannot be answered from the data, say so clearly.
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Answer based only on the provided data profile. Be accurate and specific.",
            temperature=0.1
        )


if __name__ == "__main__":
    print("DataProfiler module loaded")
