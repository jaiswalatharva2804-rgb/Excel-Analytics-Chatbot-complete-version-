"""Hybrid Handler - Combines SQL numerical analysis with RAG text insights."""
from typing import Optional, Dict, List, Any
from core import call_llm, Database, Config


class HybridHandler:
    """
    Handles complex questions requiring both numerical analysis and text insights.
    
    Use cases:
    - "Give general insight on discount trends"
    - "What patterns do you see in customer behavior?"
    - "Analyze the relationship between ratings and feedback"
    """
    
    def __init__(self, db: Database, table: str, text_column: str = None):
        """
        Initialize hybrid handler.
        
        Args:
            db: Database instance
            table: Table name
            text_column: Optional text column for RAG analysis
        """
        self.db = db
        self.table = table
        self.text_column = text_column
        self._column_info = None
    
    def _get_column_info(self) -> Dict[str, Dict]:
        """Get column metadata for analysis."""
        if self._column_info is not None:
            return self._column_info
        
        schema = self.db.get_schema(self.table)
        columns = self.db.get_columns(self.table)
        
        info = {}
        for col in columns:
            col_schema = next((c for c in schema if c["column"] == col), {})
            dtype = col_schema.get("type", "").lower()
            
            samples = self.db.sample_column(self.table, col, limit=10)
            
            is_numeric = any(t in dtype for t in ["int", "double", "float", "decimal"])
            is_date = any(t in dtype for t in ["date", "time"])
            
            # Detect semantic type
            distinct = self.db.fetch_one(
                f'SELECT COUNT(DISTINCT "{col}") FROM {self.table}'
            )[0]
            total = self.db.fetch_one(f'SELECT COUNT(*) FROM {self.table}')[0]
            unique_ratio = distinct / total if total > 0 else 0
            
            if is_numeric:
                semantic_type = "numeric"
            elif is_date:
                semantic_type = "datetime"
            elif unique_ratio < 0.1:
                semantic_type = "categorical"
            elif unique_ratio > 0.9:
                semantic_type = "identifier"
            else:
                semantic_type = "text"
            
            info[col] = {
                "dtype": dtype,
                "semantic_type": semantic_type,
                "is_numeric": is_numeric,
                "is_date": is_date,
                "samples": samples[:5],
                "distinct_count": distinct
            }
        
        self._column_info = info
        return info
    
    def _identify_relevant_columns(self, question: str) -> Dict[str, List[str]]:
        """
        Identify which columns are relevant to the question.
        
        Returns:
            Dict with 'numeric', 'categorical', 'text', 'date' column lists
        """
        col_info = self._get_column_info()
        
        # Use LLM to identify relevant columns
        columns_context = "\n".join([
            f"- {col}: {info['semantic_type']} ({info['dtype']}), samples: {info['samples'][:3]}"
            for col, info in col_info.items()
        ])
        
        prompt = f"""
Given this question and available columns, identify which columns are relevant.

Question: "{question}"

Available Columns:
{columns_context}

Return the relevant column names as a comma-separated list.
If the question is general/overview, list ALL potentially useful columns.
Output ONLY the column names, nothing else.
"""
        
        response = call_llm(
            prompt=prompt,
            system_prompt="Return only column names separated by commas.",
            temperature=0.0
        ).strip()
        
        mentioned = [c.strip() for c in response.split(",")]
        
        # Categorize relevant columns
        result = {
            "numeric": [],
            "categorical": [],
            "text": [],
            "date": []
        }
        
        for col in mentioned:
            if col in col_info:
                sem_type = col_info[col]["semantic_type"]
                if sem_type == "numeric":
                    result["numeric"].append(col)
                elif sem_type == "categorical":
                    result["categorical"].append(col)
                elif sem_type == "datetime":
                    result["date"].append(col)
                else:
                    result["text"].append(col)
        
        return result
    
    def _get_numerical_insights(self, columns: List[str]) -> str:
        """Generate numerical insights for specified columns."""
        if not columns:
            return "No numeric columns to analyze."
        
        insights = []
        
        for col in columns[:5]:  # Limit to 5 columns
            try:
                stats = self.db.fetch_one(f'''
                    SELECT 
                        COUNT(*) as cnt,
                        COUNT(DISTINCT "{col}") as distinct_cnt,
                        MIN("{col}") as min_val,
                        MAX("{col}") as max_val,
                        AVG("{col}") as avg_val,
                        MEDIAN("{col}") as median_val,
                        STDDEV("{col}") as std_dev
                    FROM {self.table}
                    WHERE "{col}" IS NOT NULL
                ''')
                
                insight = f"""
**{col}**:
- Count: {stats[0]:,}, Distinct: {stats[1]:,}
- Range: {stats[2]} to {stats[3]}
- Mean: {round(stats[4], 2) if stats[4] else 'N/A'}
- Median: {stats[5]}
- Std Dev: {round(stats[6], 2) if stats[6] else 'N/A'}
"""
                # Add distribution info
                try:
                    percentiles = self.db.fetch_one(f'''
                        SELECT 
                            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}"),
                            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}")
                        FROM {self.table}
                        WHERE "{col}" IS NOT NULL
                    ''')
                    insight += f"- IQR: {percentiles[0]} to {percentiles[1]}\n"
                except Exception:
                    pass
                
                insights.append(insight)
                
            except Exception as e:
                insights.append(f"**{col}**: Error analyzing - {str(e)[:50]}")
        
        return "\n".join(insights)
    
    def _get_categorical_insights(self, columns: List[str]) -> str:
        """Generate insights for categorical columns."""
        if not columns:
            return "No categorical columns to analyze."
        
        insights = []
        
        for col in columns[:5]:
            try:
                dist = self.db.fetch_all(f'''
                    SELECT "{col}", COUNT(*) as cnt
                    FROM {self.table}
                    WHERE "{col}" IS NOT NULL
                    GROUP BY "{col}"
                    ORDER BY cnt DESC
                    LIMIT 10
                ''')
                
                total = sum(r[1] for r in dist)
                
                insight = f"**{col}** (Top values):\n"
                for val, cnt in dist[:5]:
                    pct = round(cnt / total * 100, 1) if total > 0 else 0
                    insight += f"  - {val}: {cnt:,} ({pct}%)\n"
                
                insights.append(insight)
                
            except Exception as e:
                insights.append(f"**{col}**: Error - {str(e)[:50]}")
        
        return "\n".join(insights)
    
    def _get_trend_insights(self, date_col: str, metric_col: str) -> str:
        """Generate trend insights for a metric over time."""
        try:
            trend_data = self.db.fetch_all(f'''
                SELECT 
                    CAST("{date_col}" AS DATE) as period,
                    COUNT(*) as count,
                    AVG("{metric_col}") as avg_val,
                    SUM("{metric_col}") as total
                FROM {self.table}
                WHERE "{date_col}" IS NOT NULL AND "{metric_col}" IS NOT NULL
                GROUP BY CAST("{date_col}" AS DATE)
                ORDER BY period
                LIMIT 30
            ''')
            
            if len(trend_data) < 2:
                return f"Insufficient data points for trend analysis on {metric_col}."
            
            # Calculate trend direction
            values = [r[2] for r in trend_data if r[2] is not None]
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            first_avg = sum(first_half) / len(first_half) if first_half else 0
            second_avg = sum(second_half) / len(second_half) if second_half else 0
            
            if first_avg > 0:
                change_pct = ((second_avg - first_avg) / first_avg) * 100
            else:
                change_pct = 0
            
            direction = "increasing" if change_pct > 5 else "decreasing" if change_pct < -5 else "stable"
            
            insight = f"""
**Trend Analysis: {metric_col} over {date_col}**
- Data Points: {len(trend_data)}
- Overall Trend: {direction.upper()}
- Change: {change_pct:+.1f}%
- First Period Avg: {first_avg:.2f}
- Recent Period Avg: {second_avg:.2f}
"""
            return insight
            
        except Exception as e:
            return f"Could not analyze trend: {str(e)[:100]}"
    
    def _get_text_sample(self, constraints: Dict = None) -> List[str]:
        """Get sample text data for context."""
        if not self.text_column:
            return []
        
        try:
            where_clause = f'"{self.text_column}" IS NOT NULL'
            if constraints:
                for col, val in constraints.items():
                    if isinstance(val, str):
                        where_clause += f' AND "{col}" = \'{val}\''
            
            samples = self.db.fetch_all(f'''
                SELECT "{self.text_column}"
                FROM {self.table}
                WHERE {where_clause}
                LIMIT 10
            ''')
            
            return [str(r[0])[:200] for r in samples]
        except Exception:
            return []
    
    def _get_correlation_insights(self, num_cols: List[str], cat_cols: List[str]) -> str:
        """Analyze relationships between numeric and categorical columns."""
        if not num_cols or not cat_cols:
            return ""
        
        insights = []
        
        # Analyze first numeric column by first categorical
        num_col = num_cols[0]
        cat_col = cat_cols[0]
        
        try:
            breakdown = self.db.fetch_all(f'''
                SELECT 
                    "{cat_col}",
                    COUNT(*) as cnt,
                    AVG("{num_col}") as avg_val,
                    MIN("{num_col}") as min_val,
                    MAX("{num_col}") as max_val
                FROM {self.table}
                WHERE "{cat_col}" IS NOT NULL AND "{num_col}" IS NOT NULL
                GROUP BY "{cat_col}"
                ORDER BY avg_val DESC
                LIMIT 10
            ''')
            
            insight = f"**{num_col} by {cat_col}**:\n"
            for row in breakdown[:5]:
                insight += f"  - {row[0]}: avg={round(row[2], 2) if row[2] else 'N/A'}, "
                insight += f"range=[{row[3]}-{row[4]}], n={row[1]:,}\n"
            
            insights.append(insight)
            
        except Exception:
            pass
        
        return "\n".join(insights)
    
    def analyze(self, question: str, constraints: Optional[Dict] = None) -> str:
        """
        Perform comprehensive hybrid analysis.
        
        Args:
            question: User's question
            constraints: Optional filters to apply
            
        Returns:
            Comprehensive insights combining numerical and text analysis
        """
        # Identify relevant columns
        relevant_cols = self._identify_relevant_columns(question)
        
        # Gather insights from different sources
        insights_parts = []
        
        # Dataset overview
        total_rows = self.db.fetch_one(f'SELECT COUNT(*) FROM {self.table}')[0]
        insights_parts.append(f"**Dataset Overview**: {total_rows:,} total records\n")
        
        # Numerical insights
        if relevant_cols["numeric"]:
            num_insights = self._get_numerical_insights(relevant_cols["numeric"])
            insights_parts.append("## Numerical Analysis\n" + num_insights)
        
        # Categorical insights
        if relevant_cols["categorical"]:
            cat_insights = self._get_categorical_insights(relevant_cols["categorical"])
            insights_parts.append("## Categorical Breakdown\n" + cat_insights)
        
        # Trend analysis if date column available
        if relevant_cols["date"] and relevant_cols["numeric"]:
            trend_insights = self._get_trend_insights(
                relevant_cols["date"][0],
                relevant_cols["numeric"][0]
            )
            insights_parts.append("## Trend Analysis\n" + trend_insights)
        
        # Cross-analysis
        if relevant_cols["numeric"] and relevant_cols["categorical"]:
            corr_insights = self._get_correlation_insights(
                relevant_cols["numeric"],
                relevant_cols["categorical"]
            )
            if corr_insights:
                insights_parts.append("## Breakdown Analysis\n" + corr_insights)
        
        # Text samples for context
        text_samples = self._get_text_sample(constraints)
        if text_samples:
            insights_parts.append(
                "## Sample Text Data\n" + 
                "\n".join([f"- {s[:100]}..." if len(s) > 100 else f"- {s}" 
                          for s in text_samples[:5]])
            )
        
        # Combine all insights for LLM synthesis
        combined_insights = "\n\n".join(insights_parts)
        
        prompt = f"""
You are an expert data analyst providing comprehensive insights.

Question: "{question}"

Data Analysis Results:
{combined_insights}

Based on this analysis, provide a comprehensive answer that:

1. **Direct Answer**: Directly address the user's question with specific findings

2. **Key Insights**: 
   - What are the most important patterns or trends?
   - What stands out in the data?
   - Are there any surprising findings?

3. **Detailed Breakdown**:
   - Support your insights with specific numbers
   - Compare different segments/categories if applicable
   - Note any trends over time if relevant

4. **Implications & Recommendations**:
   - What do these findings suggest?
   - What actions or further analysis would you recommend?

Be specific, cite actual numbers from the data, and make your analysis actionable.
If any aspect cannot be answered from the available data, acknowledge this clearly.
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Provide accurate, data-driven insights. Be specific and cite actual numbers.",
            temperature=0.2
        )
    
    def general_overview(self) -> str:
        """
        Generate a general overview of the entire dataset.
        
        Returns:
            Comprehensive dataset overview with key insights
        """
        col_info = self._get_column_info()
        total_rows = self.db.fetch_one(f'SELECT COUNT(*) FROM {self.table}')[0]
        
        # Categorize columns
        numeric_cols = [c for c, info in col_info.items() if info["semantic_type"] == "numeric"]
        cat_cols = [c for c, info in col_info.items() if info["semantic_type"] == "categorical"]
        date_cols = [c for c, info in col_info.items() if info["semantic_type"] == "datetime"]
        text_cols = [c for c, info in col_info.items() if info["semantic_type"] == "text"]
        
        overview_parts = [
            f"## Dataset Overview: {self.table}",
            f"- Total Rows: {total_rows:,}",
            f"- Total Columns: {len(col_info)}",
            f"- Numeric Columns: {len(numeric_cols)}",
            f"- Categorical Columns: {len(cat_cols)}",
            f"- Date/Time Columns: {len(date_cols)}",
            f"- Text Columns: {len(text_cols)}",
            ""
        ]
        
        # Add numeric summaries
        if numeric_cols:
            overview_parts.append(self._get_numerical_insights(numeric_cols[:3]))
        
        # Add categorical summaries
        if cat_cols:
            overview_parts.append(self._get_categorical_insights(cat_cols[:3]))
        
        combined = "\n".join(overview_parts)
        
        prompt = f"""
{combined}

Provide a comprehensive overview of this dataset:

1. **What is this data about?** - Describe the nature and purpose of this dataset

2. **Key Statistics** - Summarize the most important numbers

3. **Notable Patterns** - What patterns or trends are visible?

4. **Data Quality** - Any concerns about missing data or anomalies?

5. **Suggested Analyses** - What questions would be interesting to explore?

Be specific and base everything on the actual data provided.
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Provide accurate dataset overview based on evidence.",
            temperature=0.2
        )
    
    def handle(self, question: str, constraints: Optional[Dict] = None) -> str:
        """
        Main entry point for hybrid analysis.
        
        Args:
            question: User's question
            constraints: Optional filters
            
        Returns:
            Comprehensive analysis combining multiple approaches
        """
        question_lower = question.lower()
        
        # Check for overview requests
        if any(kw in question_lower for kw in [
            "overview", "summary", "general insight", "tell me about the data",
            "what can you tell me", "describe the data", "data summary"
        ]):
            return self.general_overview()
        
        # Default to full analysis
        return self.analyze(question, constraints)


if __name__ == "__main__":
    print("HybridHandler module loaded")
