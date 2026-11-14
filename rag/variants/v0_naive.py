import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure parent directory imports (db, embedder) work correctly
sys.path.append(str(Path(__file__).parent.parent / "ingest"))

from db import get_db_connection
from embedder import get_embedding

def retrieve(query: str, index=None, k: int = 5) -> List[Dict[str, Any]]:
    """Mandatory baseline: dense top-k cosine similarity retrieval via pgvector."""
    query_vector = get_embedding(query)
    if not query_vector:
        print("❌ Failed to generate query embedding.")
        return []

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, content, metadata, 1 - (embedding <=> %s::vector) AS similarity
        FROM portfolio_vectors
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (query_vector, query_vector, k))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "content": r[1],
            "metadata": r[2],
            "similarity": round(float(r[3]), 4)
        })
    return results

if __name__ == "__main__":
    print("Testing v0_naive.py baseline retrieval...")
    res = retrieve("Python REST API", k=2)
    print(f"✅ Returned {len(res)} results.")
    for idx, item in enumerate(res, 1):
        print(f"  {idx}. {item['id']} - Similarity: {item['similarity']}")