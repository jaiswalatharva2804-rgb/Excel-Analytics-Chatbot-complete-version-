"""Question Router - Routes questions to appropriate handlers."""
import json
import re
from typing import Optional, List, Dict, Any
from core import call_llm


class QuestionRouter:
    """
    Routes questions to appropriate handlers based on question type.
    
    Supports multiple route types:
    - SQL: Structured/numeric queries
    - CLUSTER: Text grouping/frequency analysis
    - RAG: Semantic/conceptual explanation
    - SCHEMA: Data structure/column questions
    - TREND: Time-based trend analysis
    - OVERVIEW: General insights
    - HYBRID: Complex questions requiring multiple approaches
    """
    
    # Route types
    SQL = "SQL"
    CLUSTER = "CLUSTER"
    RAG = "RAG"
    SCHEMA = "SCHEMA"
    TREND = "TREND"
    OVERVIEW = "OVERVIEW"
    HYBRID = "HYBRID"
    
    # Keywords for each route type
    SCHEMA_KEYWORDS = [
        "column", "columns", "schema", "structure", "data type", "field", "fields",
        "what is in", "what does", "explain the data", "describe the data",
        "what are the", "list all column", "show column", "tell me about the column",
        "what columns", "which columns", "explain each", "describe each",
        "what information", "what data", "dataset structure"
    ]
    
    TREND_KEYWORDS = [
        "trend", "over time", "time series", "growth", "decline", "change over",
        "historical", "progression", "evolution", "pattern over", "monthly",
        "weekly", "daily", "yearly", "quarter", "seasonal"
    ]
    
    OVERVIEW_KEYWORDS = [
        "overview", "summary", "general insight", "tell me about", "describe",
        "what can you tell", "give me insight", "high level", "overall",
        "big picture", "general analysis", "key findings", "main takeaway"
    ]
    
    HYBRID_KEYWORDS = [
        "insight on", "analyze", "analysis of", "understand", "relationship between",
        "correlation", "impact of", "effect of", "compare", "breakdown"
    ]
    
    SQL_KEYWORDS = [
        "how many", "count", "average", "avg", "sum", "total",
        "list all", "show all", "display", "what is the",
        "top 10", "top ten", "top 5", "top five", "bottom",
        "highest", "lowest", "max", "min", "longest", "shortest",
        "duration", "length", "score", "rating", "number of",
        "percentage", "percent", "ratio"
    ]
    
    CLUSTER_KEYWORDS = [
        "most common", "least common", "frequent issue", "frequent complaint",
        "major theme", "minor theme", "popular complaint", "common reason",
        "main issues", "common complaints", "recurring", "categories of",
        "types of complaint", "group", "cluster", "categorize"
    ]
    
    RAG_KEYWORDS = [
        "why", "explain why", "reason for", "what caused", "how come",
        "tell me more about", "elaborate", "detail", "example of",
        "specific feedback", "what are people saying"
    ]
    
    def __init__(self, columns: List[str] = None, data_profile: Dict = None):
        """
        Initialize router.
        
        Args:
            columns: List of available column names for context
            data_profile: Optional data profile for better routing
        """
        self.columns = columns or []
        self.data_profile = data_profile or {}
    
    def _check_keywords(self, question: str, keywords: List[str]) -> bool:
        """Check if question contains any of the keywords."""
        question_lower = question.lower()
        return any(kw in question_lower for kw in keywords)
    
    def _fast_route(self, question: str) -> Optional[str]:
        """
        Fast keyword-based routing for common patterns.
        Returns None if uncertain, requiring LLM routing.
        """
        question_lower = question.lower()
        
        # SCHEMA - highest priority for column/structure questions
        if self._check_keywords(question, self.SCHEMA_KEYWORDS):
            # Verify it's really about schema, not using column values
            schema_specific = [
                "explain all column", "list all column", "what column",
                "describe the column", "tell me about column", "what are the column",
                "schema", "structure", "what does each column", "explain each column"
            ]
            if any(kw in question_lower for kw in schema_specific):
                return self.SCHEMA
        
        # TREND - time-based analysis
        if self._check_keywords(question, self.TREND_KEYWORDS):
            return self.TREND
        
        # OVERVIEW - general insights
        if self._check_keywords(question, self.OVERVIEW_KEYWORDS):
            # Check if it's a general overview vs specific
            if any(kw in question_lower for kw in ["overview", "summary", "general insight", "big picture"]):
                return self.OVERVIEW
            return self.HYBRID
        
        # HYBRID - complex analysis questions
        if self._check_keywords(question, self.HYBRID_KEYWORDS):
            # But not if it's clearly SQL
            if not self._check_keywords(question, ["how many", "count", "total", "sum"]):
                return self.HYBRID
        
        # SQL - numeric/structured queries
        if self._check_keywords(question, self.SQL_KEYWORDS):
            return self.SQL
        
        # CLUSTER - frequency/grouping
        if self._check_keywords(question, self.CLUSTER_KEYWORDS):
            return self.CLUSTER
        
        # RAG - why/explanation questions
        if self._check_keywords(question, self.RAG_KEYWORDS):
            return self.RAG
        
        return None  # Uncertain, use LLM
    
    def route(self, question: str) -> Dict[str, Any]:
        """
        Analyze question and determine routing.
        
        Args:
            question: User's question
            
        Returns:
            Dict with routing info:
            {
                "route": str,
                "constraints": {...} or None,
                "needs": {...},
                "confidence": str
            }
        """
        # Try fast routing first
        fast_result = self._fast_route(question)
        
        if fast_result:
            return {
                "route": fast_result,
                "constraints": self._extract_constraints_fast(question),
                "needs": self._infer_needs(question, fast_result),
                "confidence": "high"
            }
        
        # Fall back to LLM routing for ambiguous questions
        return self._llm_route(question)
    
    def _extract_constraints_fast(self, question: str) -> Optional[Dict]:
        """Quick constraint extraction without LLM."""
        if not self.columns:
            return None
        
        constraints = {}
        question_lower = question.lower()
        
        # Look for "in X", "for X", "where X is Y" patterns
        for col in self.columns:
            col_lower = col.lower()
            
            # Pattern: "in {column} = {value}" or "for {column} {value}"
            patterns = [
                rf"in\s+{re.escape(col_lower)}\s*[=:]?\s*[\"']?([\w\s]+)[\"']?",
                rf"for\s+{re.escape(col_lower)}\s*[=:]?\s*[\"']?([\w\s]+)[\"']?",
                rf"where\s+{re.escape(col_lower)}\s*(?:is|=)\s*[\"']?([\w\s]+)[\"']?",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, question_lower)
                if match:
                    value = match.group(1).strip()
                    if value and len(value) < 50:  # Sanity check
                        constraints[col] = value
                        break
        
        return constraints if constraints else None
    
    def _infer_needs(self, question: str, route: str) -> Dict[str, bool]:
        """Infer what the question needs based on route and keywords."""
        question_lower = question.lower()
        
        return {
            "aggregation": route == self.SQL or any(
                kw in question_lower for kw in ["total", "sum", "average", "count"]
            ),
            "explanation": route in [self.RAG, self.OVERVIEW, self.HYBRID] or any(
                kw in question_lower for kw in ["why", "explain", "reason"]
            ),
            "frequency": route == self.CLUSTER or any(
                kw in question_lower for kw in ["common", "frequent", "recurring"]
            ),
            "trend": route == self.TREND or any(
                kw in question_lower for kw in ["trend", "over time", "change"]
            ),
            "schema": route == self.SCHEMA
        }
    
    def _llm_route(self, question: str) -> Dict[str, Any]:
        """
        Use LLM for complex routing decisions.
        """
        column_info = ""
        if self.columns:
            column_info = f"Available columns: {', '.join(self.columns[:20])}"  # Limit columns
        
        prompt = f"""
You are a query routing engine for a data analytics chatbot.

Analyze this question and determine the best route.

{column_info}

ROUTING OPTIONS:

1. SCHEMA → Questions about data structure, columns, what data is available
   Examples: "What columns are there?", "Explain the columns", "What data do you have?"

2. SQL → Numeric/structured queries requiring database aggregation
   Examples: "How many?", "Average of X", "Top 10 by Y", "Total sales"

3. CLUSTER → Finding patterns/themes in TEXT data
   Examples: "Most common complaints", "Main issues", "Frequent problems"

4. RAG → Why/explanation questions using text context
   Examples: "Why are customers unhappy?", "Explain the issues"

5. TREND → Time-based analysis
   Examples: "How has X changed over time?", "Sales trend"

6. OVERVIEW → General dataset insights
   Examples: "Give me an overview", "Summarize the data"

7. HYBRID → Complex questions needing multiple analysis types
   Examples: "Analyze the relationship between X and Y", "Insights on discount trends"

Question: "{question}"

Return ONLY valid JSON:
{{
  "route": "SCHEMA" | "SQL" | "CLUSTER" | "RAG" | "TREND" | "OVERVIEW" | "HYBRID",
  "constraints": {{"column": "value"}} or null,
  "reasoning": "brief explanation"
}}
"""
        
        try:
            response = call_llm(
                prompt=prompt,
                system_prompt="Output only valid JSON. No markdown.",
                temperature=0.0
            )
            
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r"```json?\n?", "", response)
                response = response.replace("```", "")
            
            result = json.loads(response)
            
            # Validate route
            valid_routes = [self.SQL, self.CLUSTER, self.RAG, self.SCHEMA, 
                           self.TREND, self.OVERVIEW, self.HYBRID]
            if result.get("route") not in valid_routes:
                result["route"] = self.HYBRID  # Default to hybrid for uncertain
            
            return {
                "route": result["route"],
                "constraints": result.get("constraints"),
                "needs": self._infer_needs(question, result["route"]),
                "confidence": "medium"
            }
            
        except (json.JSONDecodeError, Exception):
            # Fallback to keyword-based routing
            return {
                "route": self._fallback_route(question),
                "constraints": None,
                "needs": {
                    "aggregation": False,
                    "explanation": True,
                    "frequency": False,
                    "trend": False,
                    "schema": False
                },
                "confidence": "low"
            }
    
    def _fallback_route(self, question: str) -> str:
        """Last resort keyword-based fallback routing."""
        question_lower = question.lower()
        
        # Check each category in priority order
        if any(kw in question_lower for kw in ["column", "schema", "structure", "explain all"]):
            return self.SCHEMA
        
        if any(kw in question_lower for kw in self.SQL_KEYWORDS):
            return self.SQL
        
        if any(kw in question_lower for kw in self.CLUSTER_KEYWORDS):
            return self.CLUSTER
        
        if any(kw in question_lower for kw in self.TREND_KEYWORDS):
            return self.TREND
        
        if any(kw in question_lower for kw in self.OVERVIEW_KEYWORDS):
            return self.OVERVIEW
        
        # Default to HYBRID for complex/unclear questions
        return self.HYBRID
    
    def extract_constraints(self, question: str, columns: List[str]) -> Optional[Dict]:
        """
        Extract constraints from question using LLM.
        
        Args:
            question: User question
            columns: Available column names
            
        Returns:
            Dict of constraints or None
        """
        # Try fast extraction first
        fast_constraints = self._extract_constraints_fast(question)
        if fast_constraints:
            return fast_constraints
        
        # Fall back to LLM
        prompt = f"""
Extract any explicit filters from this question.

Available columns: {', '.join(columns[:20])}

Rules:
- Only extract EXPLICITLY mentioned filters
- Match to available columns
- Return JSON object or null if no filters

Question: {question}

Return ONLY: {{"column": "value"}} or null
"""
        
        try:
            response = call_llm(
                prompt=prompt,
                system_prompt="Return only JSON or null.",
                temperature=0.0
            ).strip()
            
            if response.lower() == "null":
                return None
            
            return json.loads(response)
        except (json.JSONDecodeError, Exception):
            return None


if __name__ == "__main__":
    router = QuestionRouter(columns=["rating", "feedback", "date", "category"])
    
    # Test routing with comprehensive examples
    test_questions = [
        # SCHEMA questions
        ("What columns are available?", "SCHEMA"),
        ("Explain all the columns", "SCHEMA"),
        ("What does each column mean?", "SCHEMA"),
        
        # SQL questions  
        ("How many employees are there?", "SQL"),
        ("Show average salary by department", "SQL"),
        ("What is the total revenue?", "SQL"),
        ("Top 10 highest rated products", "SQL"),
        
        # CLUSTER questions
        ("What is the most common complaint?", "CLUSTER"),
        ("What are the main issues customers mention?", "CLUSTER"),
        
        # RAG questions
        ("Why are customers unhappy with delivery?", "RAG"),
        ("Explain why sales dropped", "RAG"),
        
        # TREND questions
        ("How has sales changed over time?", "TREND"),
        ("Show me the monthly trend", "TREND"),
        
        # OVERVIEW questions
        ("Give me an overview of the data", "OVERVIEW"),
        ("Summarize the dataset", "OVERVIEW"),
        
        # HYBRID questions
        ("Analyze the relationship between price and rating", "HYBRID"),
        ("Give me insights on discount trends", "HYBRID"),
    ]
    
    print("Testing QuestionRouter")
    print("=" * 60)
    
    correct = 0
    for question, expected in test_questions:
        result = router.route(question)
        actual = result["route"]
        status = "✓" if actual == expected else "✗"
        if actual == expected:
            correct += 1
        print(f"{status} Q: {question}")
        print(f"   Expected: {expected}, Got: {actual}")
        print()
    
    print(f"\nAccuracy: {correct}/{len(test_questions)} ({correct/len(test_questions)*100:.0f}%)")
