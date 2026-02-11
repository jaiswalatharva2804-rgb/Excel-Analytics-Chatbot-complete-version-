"""RAG Handler for descriptive/semantic queries with sub-question generation."""
import json
from typing import Optional
import numpy as np

from core import call_llm, embed, Database, Config
from utils import VectorStore


class RAGHandler:
    """Handles RAG-based queries using sub-question decomposition for better retrieval."""
    
    def __init__(self, db: Database, table: str, text_column: str):
        """
        Initialize RAG handler.
        
        Args:
            db: Database instance
            table: Table name
            text_column: Column containing text for RAG
        """
        self.db = db
        self.table = table
        self.text_column = text_column
        self._texts = None
        self._vector_store = None
    
    def _load_texts(self, constraints: Optional[dict] = None) -> list[str]:
        """Load text data from database."""
        return self.db.get_text_column_data(
            self.table,
            self.text_column,
            constraints
        )
    
    def build_index(self, constraints: Optional[dict] = None):
        """
        Build vector index from database text data.
        
        Args:
            constraints: Optional filters to apply
        """
        self._texts = self._load_texts(constraints)
        
        if not self._texts:
            raise ValueError(f"No text data found in column '{self.text_column}'")
        
        embeddings = embed(self._texts)
        self._vector_store = VectorStore(embeddings)
    
    def generate_sub_questions(self, question: str) -> list[str]:
        """
        Generate 5-6 sub-questions to retrieve more relevant content.
        
        Args:
            question: Original user question
            
        Returns:
            List of sub-questions for retrieval
        """
        prompt = f"""
You are a question decomposition expert for a customer feedback analysis system.

Given a user question, generate 5-6 diverse sub-questions that will help retrieve
the most relevant feedback/reviews from a database.

GOALS:
- Cover different aspects of the original question
- Use different phrasings and synonyms
- Include specific and general variations
- Think about what customers might actually say

Original Question: "{question}"

Generate 5-6 sub-questions as a JSON array:
["sub-question 1", "sub-question 2", ...]

Output ONLY the JSON array, no explanations.
"""
        
        response = call_llm(
            prompt=prompt,
            system_prompt="Output only valid JSON array.",
            temperature=0.3
        )
        
        try:
            sub_questions = json.loads(response)
            # Always include the original question
            return [question] + sub_questions[:5]
        except json.JSONDecodeError:
            # Fallback: return original question with variations
            return [
                question,
                f"What do customers say about {question.lower()}?",
                f"Customer complaints regarding {question.lower()}",
                f"Feedback about {question.lower()}",
                f"Issues related to {question.lower()}"
            ]
    
    def search(self, query: str, k: int = None) -> list[str]:
        """
        Search for relevant texts.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of relevant text passages
        """
        if self._vector_store is None:
            raise ValueError("Index not built. Call build_index() first.")
        
        k = k or Config.RAG_TOP_K
        
        # Embed query
        query_embedding = embed([query])
        
        # Search
        indices = self._vector_store.search(query_embedding, k=k)
        
        return [self._texts[i] for i in indices]
    
    def multi_query_search(self, questions: list[str], k_per_query: int = 3) -> list[str]:
        """
        Search using multiple queries and deduplicate results.
        
        Args:
            questions: List of search queries
            k_per_query: Results per query
            
        Returns:
            Deduplicated list of relevant texts
        """
        all_results = []
        seen = set()
        
        for query in questions:
            results = self.search(query, k=k_per_query)
            for text in results:
                if text not in seen:
                    seen.add(text)
                    all_results.append(text)
        
        return all_results
    
    def explain(self, context_texts: list[str], question: str, 
                sub_questions: list[str] = None) -> str:
        """
        Use LLM to synthesize and explain retrieved context.
        
        Args:
            context_texts: Retrieved text passages
            question: Original question
            sub_questions: Sub-questions used for retrieval
            
        Returns:
            Comprehensive explanation
        """
        context = "\n---\n".join(context_texts)
        
        sub_q_text = ""
        if sub_questions:
            sub_q_text = f"\nAspects explored:\n" + "\n".join(f"- {q}" for q in sub_questions[1:])
        
        system_prompt = """
You are an expert customer insights analyst.

Your task is to provide a comprehensive, well-structured analysis based on customer feedback.
"""
        
        user_prompt = f"""
Original Question: {question}
{sub_q_text}

Relevant Customer Feedback:
{context}

Provide a thorough analysis:

1. **Direct Answer**: Answer the question based on the feedback

2. **Key Themes**: Identify 2-3 main themes from the feedback

3. **Specific Examples**: Quote or reference specific feedback that supports your answer

4. **Insights**: What patterns or notable observations do you see?

Be specific and ground your analysis in the actual feedback provided.
If the context doesn't fully answer the question, acknowledge the limitations.
"""
        
        return call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2
        )
    
    def handle(self, question: str, constraints: Optional[dict] = None) -> str:
        """
        Full RAG pipeline with sub-question generation.
        
        Pipeline:
        1. Generate sub-questions from user question
        2. Search using all sub-questions
        3. Deduplicate and combine results
        4. Generate comprehensive explanation
        
        Args:
            question: Natural language question
            constraints: Optional filters to apply
            
        Returns:
            Natural language response
        """
        try:
            # Build index with constraints
            self.build_index(constraints)
            
            # Generate sub-questions for better retrieval
            sub_questions = self.generate_sub_questions(question)
            
            # Multi-query retrieval
            context = self.multi_query_search(sub_questions, k_per_query=3)
            
            # Limit total context to avoid token overflow
            context = context[:12]
            
            # Generate comprehensive explanation
            return self.explain(context, question, sub_questions)
            
        except Exception as e:
            return f"Error processing query: {str(e)}"


if __name__ == "__main__":
    print("RAGHandler module loaded")
