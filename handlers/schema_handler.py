"""Schema Handler - Handles questions about data structure, columns, and schema."""
from typing import Optional, List, Dict, Any
from core import call_llm, Database


class SchemaHandler:
    """Handles questions about data schema, columns, and structure."""
    
    def __init__(self, db: Database, table: str):
        """
        Initialize schema handler.
        
        Args:
            db: Database instance
            table: Table name
        """
        self.db = db
        self.table = table
        self._column_profiles = None
    
    def _get_column_profile(self, column: str) -> Dict[str, Any]:
        """Get detailed profile for a single column."""
        schema = self.db.get_schema(self.table)
        col_info = next((c for c in schema if c["column"] == column), None)
        
        if not col_info:
            return {"error": f"Column '{column}' not found"}
        
        dtype = col_info["type"]
        
        # Get statistics
        total = self.db.fetch_one(f'SELECT COUNT(*) FROM {self.table}')[0]
        null_count = self.db.fetch_one(
            f'SELECT COUNT(*) FROM {self.table} WHERE "{column}" IS NULL'
        )[0]
        distinct = self.db.fetch_one(
            f'SELECT COUNT(DISTINCT "{column}") FROM {self.table}'
        )[0]
        
        # Get sample values
        samples = self.db.sample_column(self.table, column, limit=10)
        
        profile = {
            "name": column,
            "data_type": dtype,
            "total_rows": total,
            "null_count": null_count,
            "null_pct": round(null_count / total * 100, 1) if total > 0 else 0,
            "distinct_count": distinct,
            "unique_pct": round(distinct / total * 100, 1) if total > 0 else 0,
            "samples": samples[:5]
        }
        
        # Add numeric statistics if applicable
        if any(t in dtype.lower() for t in ["int", "double", "float", "decimal"]):
            try:
                stats = self.db.fetch_one(f'''
                    SELECT 
                        MIN("{column}"), MAX("{column}"), 
                        AVG("{column}"), MEDIAN("{column}")
                    FROM {self.table}
                    WHERE "{column}" IS NOT NULL
                ''')
                profile["min"] = stats[0]
                profile["max"] = stats[1]
                profile["mean"] = round(stats[2], 2) if stats[2] else None
                profile["median"] = stats[3]
            except Exception:
                pass
        
        # Add value distribution for low-cardinality columns
        if distinct <= 20:
            try:
                dist = self.db.fetch_all(f'''
                    SELECT "{column}", COUNT(*) as cnt
                    FROM {self.table}
                    WHERE "{column}" IS NOT NULL
                    GROUP BY "{column}"
                    ORDER BY cnt DESC
                    LIMIT 10
                ''')
                profile["top_values"] = {str(row[0]): row[1] for row in dist}
            except Exception:
                pass
        
        return profile
    
    def _get_all_column_profiles(self) -> Dict[str, Dict]:
        """Get profiles for all columns (cached)."""
        if self._column_profiles is None:
            columns = self.db.get_columns(self.table)
            self._column_profiles = {}
            for col in columns:
                try:
                    self._column_profiles[col] = self._get_column_profile(col)
                except Exception as e:
                    self._column_profiles[col] = {"error": str(e)}
        return self._column_profiles
    
    def _format_column_info(self, profile: Dict) -> str:
        """Format a column profile for display."""
        if "error" in profile:
            return f"  Error: {profile['error']}"
        
        lines = [
            f"  • Data Type: {profile['data_type']}",
            f"  • Total Rows: {profile['total_rows']:,}",
            f"  • Missing Values: {profile['null_count']:,} ({profile['null_pct']}%)",
            f"  • Unique Values: {profile['distinct_count']:,} ({profile['unique_pct']}%)",
        ]
        
        if profile.get("min") is not None:
            lines.append(f"  • Range: {profile['min']} to {profile['max']}")
            lines.append(f"  • Mean: {profile['mean']}, Median: {profile['median']}")
        
        if profile.get("top_values"):
            top_3 = list(profile["top_values"].items())[:3]
            vals = ", ".join([f"'{k}' ({v})" for k, v in top_3])
            lines.append(f"  • Top Values: {vals}")
        
        if profile.get("samples"):
            samples_str = ", ".join([f"'{s[:30]}...'" if len(str(s)) > 30 else f"'{s}'" 
                                    for s in profile["samples"][:3]])
            lines.append(f"  • Sample Values: {samples_str}")
        
        return "\n".join(lines)
    
    def explain_all_columns(self) -> str:
        """
        Generate comprehensive explanation of all columns.
        
        Returns:
            Detailed explanation of every column in the dataset
        """
        profiles = self._get_all_column_profiles()
        total_rows = self.db.fetch_one(f'SELECT COUNT(*) FROM {self.table}')[0]
        
        # Build detailed context for LLM
        column_details = []
        for col, profile in profiles.items():
            if "error" in profile:
                column_details.append(f"\n**{col}**: Error reading column")
                continue
            
            detail = f"\n**{col}**:\n"
            detail += f"  Type: {profile['data_type']}\n"
            detail += f"  Distinct: {profile['distinct_count']} ({profile['unique_pct']}% unique)\n"
            detail += f"  Missing: {profile['null_pct']}%\n"
            detail += f"  Samples: {profile.get('samples', [])[:5]}\n"
            
            if profile.get("min") is not None:
                detail += f"  Range: {profile['min']} - {profile['max']}, Mean: {profile['mean']}\n"
            if profile.get("top_values"):
                detail += f"  Categories: {list(profile['top_values'].keys())[:5]}\n"
            
            column_details.append(detail)
        
        prompt = f"""
You are a data analyst explaining a dataset to a business user.

Dataset: {self.table}
Total Rows: {total_rows:,}
Total Columns: {len(profiles)}

Column Details:
{''.join(column_details)}

Provide a clear, comprehensive explanation of ALL columns in this dataset:

For EACH column, explain:
1. **What it represents** - What does this column likely store? (based on name, type, and sample values)
2. **Data characteristics** - Is it numeric, categorical, text, date? High or low cardinality?
3. **Key observations** - Any notable patterns? Missing data concerns? Unusual values?

After explaining each column, provide:
- **Dataset Overview**: What kind of data is this overall?
- **Relationships**: How might columns relate to each other?
- **Potential Uses**: What analyses would this data support?

Be specific, use actual column names, and base everything on the evidence provided.
"""
        
        response = call_llm(
            prompt=prompt,
            system_prompt="Explain data columns clearly and accurately. Base explanations only on provided evidence.",
            temperature=0.1
        )
        
        return response
    
    def explain_column(self, column: str) -> str:
        """
        Explain a specific column in detail.
        
        Args:
            column: Column name to explain
            
        Returns:
            Detailed explanation of the column
        """
        profile = self._get_column_profile(column)
        
        if "error" in profile:
            # Try fuzzy match
            columns = self.db.get_columns(self.table)
            matches = [c for c in columns if column.lower() in c.lower()]
            if matches:
                return f"Column '{column}' not found. Did you mean: {', '.join(matches)}?"
            return f"Column '{column}' not found. Available columns: {', '.join(columns)}"
        
        # Build detailed context
        context = f"""
Column: {profile['name']}
Data Type: {profile['data_type']}
Total Rows: {profile['total_rows']:,}
Missing Values: {profile['null_count']:,} ({profile['null_pct']}%)
Unique Values: {profile['distinct_count']:,} ({profile['unique_pct']}%)
Sample Values: {profile.get('samples', [])}
"""
        if profile.get("min") is not None:
            context += f"Min: {profile['min']}, Max: {profile['max']}\n"
            context += f"Mean: {profile['mean']}, Median: {profile['median']}\n"
        
        if profile.get("top_values"):
            context += f"Value Distribution: {profile['top_values']}\n"
        
        prompt = f"""
{context}

Explain this column in detail:
1. What does this column likely represent?
2. What type of data does it contain?
3. What are the key characteristics? (range, common values, missing data)
4. Any notable observations or potential issues?
5. How might this column be used in analysis?

Be specific and base your explanation on the actual data shown.
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Explain data columns accurately based on evidence.",
            temperature=0.1
        )
    
    def list_columns(self) -> str:
        """
        List all columns with brief descriptions.
        
        Returns:
            Formatted list of columns
        """
        profiles = self._get_all_column_profiles()
        
        output = [f"📊 **Dataset: {self.table}**\n"]
        output.append(f"Total Columns: {len(profiles)}\n")
        output.append("-" * 50 + "\n")
        
        for col, profile in profiles.items():
            if "error" in profile:
                output.append(f"\n❌ **{col}**: Error reading column\n")
                continue
            
            # Determine column category
            dtype = profile['data_type'].lower()
            if any(t in dtype for t in ["int", "double", "float"]):
                icon = "🔢"  # Numeric
                category = "Numeric"
            elif "varchar" in dtype or "char" in dtype:
                if profile['unique_pct'] < 10:
                    icon = "📋"  # Categorical
                    category = "Categorical"
                else:
                    icon = "📝"  # Text
                    category = "Text"
            elif "date" in dtype or "time" in dtype:
                icon = "📅"  # Date
                category = "Date/Time"
            elif "bool" in dtype:
                icon = "✅"  # Boolean
                category = "Boolean"
            else:
                icon = "📄"
                category = dtype
            
            output.append(f"\n{icon} **{col}** ({category})")
            output.append(self._format_column_info(profile))
        
        return "\n".join(output)
    
    def answer_schema_question(self, question: str) -> str:
        """
        Answer any question about the data schema/structure.
        
        Args:
            question: User's question about columns/structure
            
        Returns:
            Answer based on actual data profile
        """
        question_lower = question.lower()
        
        # Check for specific patterns
        if any(kw in question_lower for kw in ["list all column", "show all column", 
                                                "what column", "which column",
                                                "all the column", "column name"]):
            return self.list_columns()
        
        if any(kw in question_lower for kw in ["explain all", "describe all", 
                                                "tell me about all", "what does each"]):
            return self.explain_all_columns()
        
        # Check for specific column question
        columns = self.db.get_columns(self.table)
        mentioned_cols = [c for c in columns if c.lower() in question_lower]
        
        if len(mentioned_cols) == 1:
            return self.explain_column(mentioned_cols[0])
        
        # General schema question - use LLM with full context
        profiles = self._get_all_column_profiles()
        total_rows = self.db.fetch_one(f'SELECT COUNT(*) FROM {self.table}')[0]
        
        context = f"""
Dataset: {self.table}
Total Rows: {total_rows:,}
Columns: {len(profiles)}

Column Information:
"""
        for col, profile in profiles.items():
            if "error" in profile:
                context += f"\n{col}: [Error]\n"
                continue
            
            context += f"\n{col}:\n"
            context += f"  Type: {profile['data_type']}\n"
            context += f"  Distinct: {profile['distinct_count']} ({profile['unique_pct']}% unique)\n"
            context += f"  Missing: {profile['null_pct']}%\n"
            context += f"  Samples: {profile.get('samples', [])[:3]}\n"
            
            if profile.get("min") is not None:
                context += f"  Range: {profile['min']} - {profile['max']}\n"
            if profile.get("top_values"):
                context += f"  Top Values: {list(profile['top_values'].keys())[:5]}\n"
        
        prompt = f"""
You are a data expert answering questions about a dataset's structure.

{context}

Question: {question}

Answer the question thoroughly using ONLY the information provided above.
Be specific - cite actual column names, data types, values, and statistics.
If the question cannot be fully answered from the data, acknowledge what's missing.
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Answer schema questions accurately based only on provided data. Be specific and thorough.",
            temperature=0.1
        )
    
    def handle(self, question: str, constraints: Optional[dict] = None) -> str:
        """
        Main entry point for schema questions.
        
        Args:
            question: User's question
            constraints: Optional constraints (not used for schema questions)
            
        Returns:
            Answer about schema/columns
        """
        return self.answer_schema_question(question)


if __name__ == "__main__":
    print("SchemaHandler module loaded")
