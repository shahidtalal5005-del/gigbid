import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure ingest modules can be imported
sys.path.append(str(Path(__file__).parent / "ingest"))

from db import get_db_connection
from embedder import get_embedding

def search_portfolio(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Embeds a query string and retrieves top_k relevant portfolio items using pgvector."""
    query_vector = get_embedding(query)
    if not query_vector:
        print("❌ Failed to generate query embedding.")
        return []

    conn = get_db_connection()
    cur = conn.cursor()

    # Cosine distance operator (<=>) in pgvector
    cur.execute("""
        SELECT id, content, metadata, 1 - (embedding <=> %s::vector) AS similarity
        FROM portfolio_vectors
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (query_vector, query_vector, top_k))

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
    test_query = "Python REST API and backend microservices"
    print(f"Searching portfolio vectors for: '{test_query}'...\n")
    matches = search_portfolio(test_query, top_k=2)
    
    if matches:
        print(f"✅ Found {len(matches)} matching portfolio items:\n")
        for idx, match in enumerate(matches, 1):
            print(f"--- Result {idx} (Similarity: {match['similarity']}) ---")
            print(f"ID: {match['id']}")
            print(f"Content:\n{match['content']}\n")
    else:
        print("❌ No matching results found.")