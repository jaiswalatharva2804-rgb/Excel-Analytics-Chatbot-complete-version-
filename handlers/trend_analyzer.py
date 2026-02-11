"""Trend Analyzer - Time-based analysis and trend detection."""
from typing import Optional, List
from core import call_llm, Database, Config


class TrendAnalyzer:
    """Analyzes trends, patterns over time, and provides insights."""
    
    def __init__(self, db: Database, table: str):
        """
        Initialize trend analyzer.
        
        Args:
            db: Database instance
            table: Table name
        """
        self.db = db
        self.table = table
        self._date_columns = None
        self._numeric_columns = None
    
    def _detect_date_columns(self) -> List[str]:
        """Detect columns that contain date/time data."""
        if self._date_columns is not None:
            return self._date_columns
        
        schema = self.db.get_schema(self.table)
        columns = self.db.get_columns(self.table)
        
        date_cols = []
        for col_info in schema:
            col = col_info["column"]
            dtype = col_info["type"].lower()
            
            # Check type
            if "date" in dtype or "time" in dtype:
                date_cols.append(col)
                continue
            
            # Check column name
            date_keywords = ["date", "time", "timestamp", "created", "updated", "day", "month", "year"]
            if any(kw in col.lower() for kw in date_keywords):
                date_cols.append(col)
                continue
            
            # Check sample values
            try:
                samples = self.db.sample_column(self.table, col, limit=5)
                if samples:
                    sample = str(samples[0])
                    # Check for date patterns
                    if any(p in sample for p in ["-", "/"]) and any(c.isdigit() for c in sample):
                        if len(sample) >= 8 and len(sample) <= 25:
                            date_cols.append(col)
            except:
                pass
        
        self._date_columns = date_cols
        return date_cols
    
    def _detect_numeric_columns(self) -> List[str]:
        """Detect numeric columns for trend analysis."""
        if self._numeric_columns is not None:
            return self._numeric_columns
        
        schema = self.db.get_schema(self.table)
        
        numeric_cols = []
        for col_info in schema:
            dtype = col_info["type"].lower()
            if "int" in dtype or "double" in dtype or "float" in dtype or "decimal" in dtype:
                numeric_cols.append(col_info["column"])
        
        self._numeric_columns = numeric_cols
        return numeric_cols
    
    def _identify_relevant_column(self, question: str, columns: List[str]) -> Optional[str]:
        """Use LLM to identify which column the question refers to."""
        if not columns:
            return None
        
        if len(columns) == 1:
            return columns[0]
        
        prompt = f"""
Given this question and list of columns, identify which column is most relevant.

Question: {question}

Available columns: {columns}

Return ONLY the exact column name, nothing else.
If no column matches, return "NONE".
"""
        
        result = call_llm(
            prompt=prompt,
            system_prompt="Return only the column name.",
            temperature=0.0
        ).strip()
        
        if result in columns:
            return result
        return columns[0]  # Default to first
    
    def analyze_trend(self, question: str, metric_column: str = None, 
                     date_column: str = None) -> str:
        """
        Analyze trend for a metric over time.
        
        Args:
            question: User's question about trends
            metric_column: Column to analyze (auto-detected if None)
            date_column: Date column for time axis (auto-detected if None)
            
        Returns:
            Trend analysis with insights
        """
        # Auto-detect columns if not provided
        date_cols = self._detect_date_columns()
        numeric_cols = self._detect_numeric_columns()
        
        if not date_cols:
            return "No date/time columns found in the data. Cannot perform trend analysis."
        
        if not numeric_cols:
            return "No numeric columns found for trend analysis."
        
        date_column = date_column or self._identify_relevant_column(question, date_cols)
        metric_column = metric_column or self._identify_relevant_column(question, numeric_cols)
        
        if not date_column or not metric_column:
            return "Could not identify appropriate columns for trend analysis."
        
        # Get trend data - aggregate by date
        try:
            # Try to extract date part for grouping
            trend_query = f'''
                SELECT 
                    CAST("{date_column}" AS DATE) as period,
                    COUNT(*) as count,
                    AVG("{metric_column}") as avg_value,
                    SUM("{metric_column}") as total,
                    MIN("{metric_column}") as min_val,
                    MAX("{metric_column}") as max_val
                FROM {self.table}
                WHERE "{date_column}" IS NOT NULL AND "{metric_column}" IS NOT NULL
                GROUP BY CAST("{date_column}" AS DATE)
                ORDER BY period
            '''
            
            results = self.db.fetch_all(trend_query)
            
            if not results or len(results) < 2:
                return f"Insufficient data points for trend analysis on {metric_column}."
            
        except Exception as e:
            # Fallback: try without date casting
            try:
                trend_query = f'''
                    SELECT 
                        "{date_column}" as period,
                        COUNT(*) as count,
                        AVG("{metric_column}") as avg_value,
                        SUM("{metric_column}") as total
                    FROM {self.table}
                    WHERE "{date_column}" IS NOT NULL AND "{metric_column}" IS NOT NULL
                    GROUP BY "{date_column}"
                    ORDER BY "{date_column}"
                    LIMIT 50
                '''
                results = self.db.fetch_all(trend_query)
            except Exception as e2:
                return f"Error analyzing trend: {str(e2)}"
        
        # Calculate trend statistics
        if results:
            values = [r[2] for r in results if r[2] is not None]  # avg_value
            
            if len(values) >= 2:
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                
                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)
                
                if first_avg > 0:
                    change_pct = ((second_avg - first_avg) / first_avg) * 100
                else:
                    change_pct = 0
                
                trend_direction = "increasing" if change_pct > 5 else "decreasing" if change_pct < -5 else "stable"
            else:
                change_pct = 0
                trend_direction = "insufficient data"
        
        # Format data for LLM
        data_summary = f"""
Trend Analysis for: {metric_column}
Time Period Column: {date_column}
Data Points: {len(results)}

Trend Data (period, count, avg, total):
"""
        for r in results[:20]:  # Limit to 20 rows for LLM
            data_summary += f"  {r[0]}: count={r[1]}, avg={round(r[2], 2) if r[2] else 'N/A'}, total={r[3]}\n"
        
        if len(results) > 20:
            data_summary += f"  ... and {len(results) - 20} more periods\n"
        
        data_summary += f"""
Computed Statistics:
- Overall Trend: {trend_direction}
- Change: {change_pct:.1f}% (first half vs second half average)
- First period avg: {first_avg:.2f}
- Last period avg: {second_avg:.2f}
"""
        
        prompt = f"""
You are a data analyst providing trend insights.

Question: {question}

{data_summary}

Provide a comprehensive trend analysis:

1. **Trend Summary**: Is the metric increasing, decreasing, or stable?

2. **Key Observations**:
   - Notable peaks or dips
   - Patterns (seasonal, cyclical, etc.)
   - Any anomalies

3. **Quantified Insights**:
   - Specific percentage changes
   - Comparison between periods
   - Rate of change

4. **Business Implications**:
   - What might be causing this trend?
   - What actions might be warranted?

Be specific and use the actual numbers from the data.
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Provide accurate, data-driven trend analysis.",
            temperature=0.2
        )
    
    def analyze_distribution(self, column: str) -> str:
        """Analyze the distribution of values in a column."""
        # Check if numeric
        numeric_cols = self._detect_numeric_columns()
        
        if column in numeric_cols:
            # Numeric distribution
            query = f'''
                SELECT 
                    MIN("{column}") as min_val,
                    MAX("{column}") as max_val,
                    AVG("{column}") as mean,
                    MEDIAN("{column}") as median,
                    STDDEV("{column}") as std_dev,
                    COUNT(*) as total,
                    COUNT(DISTINCT "{column}") as distinct_vals
                FROM {self.table}
                WHERE "{column}" IS NOT NULL
            '''
            stats = self.db.fetch_one(query)
            
            # Get percentiles
            percentile_query = f'''
                SELECT 
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{column}") as p25,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{column}") as p75
                FROM {self.table}
                WHERE "{column}" IS NOT NULL
            '''
            try:
                percentiles = self.db.fetch_one(percentile_query)
            except:
                percentiles = (None, None)
            
            context = f"""
Distribution Analysis for: {column}

Statistics:
- Count: {stats[5]}
- Distinct Values: {stats[6]}
- Min: {stats[0]}
- Max: {stats[1]}
- Mean: {round(stats[2], 2) if stats[2] else 'N/A'}
- Median: {stats[3]}
- Std Dev: {round(stats[4], 2) if stats[4] else 'N/A'}
- 25th Percentile: {percentiles[0]}
- 75th Percentile: {percentiles[1]}
"""
        else:
            # Categorical distribution
            query = f'''
                SELECT "{column}", COUNT(*) as cnt
                FROM {self.table}
                WHERE "{column}" IS NOT NULL
                GROUP BY "{column}"
                ORDER BY cnt DESC
                LIMIT 20
            '''
            results = self.db.fetch_all(query)
            
            total = sum(r[1] for r in results)
            
            context = f"""
Distribution Analysis for: {column}

Value Counts (top 20):
"""
            for val, cnt in results:
                pct = (cnt / total * 100) if total > 0 else 0
                context += f"  {val}: {cnt} ({pct:.1f}%)\n"
        
        prompt = f"""
{context}

Provide insights on this distribution:
1. What is the shape of the distribution?
2. Are there any outliers or unusual patterns?
3. What does this tell us about the data?
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Analyze data distributions accurately.",
            temperature=0.2
        )
    
    def general_insights(self, focus_area: str = None) -> str:
        """
        Generate general insights about the data.
        
        Args:
            focus_area: Optional specific area to focus on
            
        Returns:
            General data insights
        """
        columns = self.db.get_columns(self.table)
        numeric_cols = self._detect_numeric_columns()
        date_cols = self._detect_date_columns()
        
        # Gather key statistics
        row_count = self.db.fetch_one(f'SELECT COUNT(*) FROM {self.table}')[0]
        
        stats_info = f"Dataset Overview:\n- Total rows: {row_count}\n- Total columns: {len(columns)}\n\n"
        
        # Numeric column stats
        if numeric_cols:
            stats_info += "Numeric Column Statistics:\n"
            for col in numeric_cols[:5]:  # Limit to 5
                try:
                    query = f'''
                        SELECT AVG("{col}"), MIN("{col}"), MAX("{col}"), STDDEV("{col}")
                        FROM {self.table}
                        WHERE "{col}" IS NOT NULL
                    '''
                    stats = self.db.fetch_one(query)
                    stats_info += f"  {col}: avg={round(stats[0], 2) if stats[0] else 'N/A'}, "
                    stats_info += f"range=[{stats[1]} - {stats[2]}]\n"
                except:
                    pass
        
        # Categorical distributions
        stats_info += "\nKey Categorical Distributions:\n"
        for col in columns:
            if col not in numeric_cols and col not in date_cols:
                try:
                    query = f'''
                        SELECT "{col}", COUNT(*) as cnt
                        FROM {self.table}
                        WHERE "{col}" IS NOT NULL
                        GROUP BY "{col}"
                        ORDER BY cnt DESC
                        LIMIT 3
                    '''
                    top_vals = self.db.fetch_all(query)
                    if top_vals and len(top_vals) <= 10:
                        stats_info += f"  {col}: {[v[0] for v in top_vals[:3]]}\n"
                except:
                    pass
        
        focus_text = f"\nFocus Area: {focus_area}" if focus_area else ""
        
        prompt = f"""
{stats_info}
{focus_text}

Generate comprehensive insights about this dataset:

1. **Data Overview**: What kind of data is this? What does it represent?

2. **Key Metrics**: What are the most important numbers to note?

3. **Notable Patterns**: Any interesting patterns or correlations visible?

4. **Data Quality**: Any concerns about missing data, outliers, or anomalies?

5. **Recommendations**: What questions would be worth exploring further?

Be specific and reference actual values from the data.
"""
        
        return call_llm(
            prompt=prompt,
            system_prompt="Provide accurate, data-driven insights.",
            temperature=0.2
        )


if __name__ == "__main__":
    print("TrendAnalyzer module loaded")
