"""Cluster Handler for frequency/grouping queries with comprehensive analysis."""
from typing import Optional
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter

from core import call_llm, embed, Database, Config


class ClusterHandler:
    """Handles clustering-based queries with detailed topic analysis."""
    
    def __init__(self, db: Database, table: str, text_column: str):
        """
        Initialize cluster handler.
        
        Args:
            db: Database instance
            table: Table name
            text_column: Column containing text to cluster
        """
        self.db = db
        self.table = table
        self.text_column = text_column
        self._texts = None
        self._embeddings = None
        self._clusters = None
        self._metadata = None  # Store additional row metadata
    
    def _load_data_with_metadata(self, constraints: Optional[dict] = None) -> tuple:
        """
        Load text data with additional metadata from database.
        
        Returns:
            Tuple of (texts, metadata_list)
        """
        # Get all columns for richer context
        columns = self.db.get_columns(self.table)
        
        # Build WHERE clause
        where_clauses = [f'"{self.text_column}" IS NOT NULL']
        if constraints:
            for col, val in constraints.items():
                if isinstance(val, str):
                    where_clauses.append(f'"{col}" = \'{val}\'')
                else:
                    where_clauses.append(f'"{col}" = {val}')
        
        where_sql = " AND ".join(where_clauses)
        
        # Select text column and a few metadata columns
        meta_columns = [c for c in columns if c != self.text_column][:5]
        select_cols = [f'"{self.text_column}"'] + [f'"{c}"' for c in meta_columns]
        
        query = f'SELECT {" , ".join(select_cols)} FROM {self.table} WHERE {where_sql}'
        rows = self.db.fetch_all(query)
        
        texts = [str(row[0]) for row in rows]
        metadata = [dict(zip(meta_columns, row[1:])) for row in rows]
        
        return texts, metadata
    
    def _compute_embeddings(self, texts: list[str]) -> np.ndarray:
        """Compute embeddings for texts."""
        return embed(texts)
    
    def _compute_clusters(self, embeddings: np.ndarray, k: int = None) -> np.ndarray:
        """Compute cluster assignments."""
        k = k or Config.DEFAULT_CLUSTERS
        # Adjust k if we have fewer samples
        k = min(k, len(embeddings))
        km = KMeans(n_clusters=k, random_state=42, n_init="auto")
        return km.fit_predict(embeddings)
    
    def build_clusters(self, constraints: Optional[dict] = None, k: int = None):
        """
        Build clusters from database text data with metadata.
        
        Args:
            constraints: Optional filters to apply
            k: Number of clusters
        """
        self._texts, self._metadata = self._load_data_with_metadata(constraints)
        
        if not self._texts:
            raise ValueError(f"No text data found in column '{self.text_column}'")
        
        self._embeddings = self._compute_embeddings(self._texts)
        self._clusters = self._compute_clusters(self._embeddings, k)
    
    def get_cluster_statistics(self) -> dict:
        """
        Get statistics about all clusters.
        
        Returns:
            Dict with cluster stats: {cluster_id: {count, percentage, sample}}
        """
        if self._clusters is None:
            raise ValueError("Clusters not built.")
        
        total = len(self._clusters)
        unique, counts = np.unique(self._clusters, return_counts=True)
        
        stats = {}
        for cluster_id, count in zip(unique, counts):
            indices = np.where(self._clusters == cluster_id)[0]
            sample_idx = indices[0]
            stats[int(cluster_id)] = {
                "count": int(count),
                "percentage": round(count / total * 100, 1),
                "sample": self._texts[sample_idx][:200]
            }
        
        # Sort by count descending
        return dict(sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True))
    
    def get_cluster_data(self, cluster_id: int, n_samples: int = 10) -> dict:
        """
        Get comprehensive data for a specific cluster.
        
        Returns:
            Dict with texts, metadata patterns, and statistics
        """
        if self._clusters is None:
            raise ValueError("Clusters not built.")
        
        indices = np.where(self._clusters == cluster_id)[0]
        
        # Get samples
        sample_indices = indices[:n_samples]
        texts = [self._texts[i] for i in sample_indices]
        metadata = [self._metadata[i] for i in sample_indices] if self._metadata else []
        
        # Analyze metadata patterns
        meta_patterns = {}
        if metadata:
            for key in metadata[0].keys():
                values = [m.get(key) for m in metadata if m.get(key)]
                if values:
                    counter = Counter(values)
                    meta_patterns[key] = dict(counter.most_common(3))
        
        return {
            "cluster_id": cluster_id,
            "total_count": len(indices),
            "texts": texts,
            "metadata_patterns": meta_patterns
        }
    
    def explain_clusters(self, question: str, top_n: int = 3) -> str:
        """
        Generate comprehensive explanation of top clusters.
        
        Args:
            question: Original question
            top_n: Number of top clusters to analyze
            
        Returns:
            Detailed analysis of clusters
        """
        stats = self.get_cluster_statistics()
        total_records = sum(s["count"] for s in stats.values())
        
        # Get detailed data for top clusters
        cluster_details = []
        for i, (cluster_id, stat) in enumerate(list(stats.items())[:top_n]):
            data = self.get_cluster_data(cluster_id, n_samples=8)
            cluster_details.append({
                "rank": i + 1,
                "count": stat["count"],
                "percentage": stat["percentage"],
                "samples": data["texts"],
                "metadata": data["metadata_patterns"]
            })
        
        # Format cluster info for LLM
        cluster_info = ""
        for detail in cluster_details:
            samples_text = "\n".join(f"  - {s[:150]}..." if len(s) > 150 else f"  - {s}" 
                                     for s in detail["samples"][:5])
            meta_text = ""
            if detail["metadata"]:
                meta_parts = [f"    {k}: {v}" for k, v in detail["metadata"].items()]
                meta_text = f"\n  Patterns:\n" + "\n".join(meta_parts)
            
            cluster_info += f"""
--- CLUSTER #{detail['rank']} ({detail['count']} records, {detail['percentage']}% of total) ---
Sample feedback:
{samples_text}{meta_text}
"""
        
        system_prompt = """
You are an expert data analyst specializing in customer feedback analysis.

Your task is to provide clear, actionable insights from clustered feedback data.
"""
        
        user_prompt = f"""
Question: {question}

Total Records Analyzed: {total_records}
Number of Clusters Found: {len(stats)}

Top {top_n} Clusters (by frequency):
{cluster_info}

Provide a comprehensive analysis:

1. **Main Finding**: Directly answer the question about what is most common/frequent

2. **Cluster Breakdown**:
   - For each cluster, give it a descriptive name/label
   - Explain what theme or issue it represents
   - Note the percentage and count

3. **Key Patterns**:
   - What are the dominant themes across all feedback?
   - Are there any surprising or notable patterns?
   - How do the clusters relate to each other?

4. **Specific Evidence**: Quote specific feedback that exemplifies each theme

5. **Recommendations**: Based on the frequency analysis, what should be prioritized?

Be specific, cite actual numbers and quotes from the data.
"""
        
        return call_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.2
        )
    
    def handle(self, question: str, constraints: Optional[dict] = None) -> str:
        """
        Full pipeline for cluster-based questions with comprehensive analysis.
        
        Args:
            question: Natural language question
            constraints: Optional filters to apply
            
        Returns:
            Detailed analysis of clusters
        """
        try:
            # Build clusters with constraints
            self.build_clusters(constraints)
            
            # Generate comprehensive explanation of top clusters
            return self.explain_clusters(question, top_n=3)
            
        except Exception as e:
            return f"Error processing cluster query: {str(e)}"


if __name__ == "__main__":
    print("ClusterHandler module loaded")
