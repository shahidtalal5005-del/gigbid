import json
from pathlib import Path
from db import get_db_connection
from embedder import get_embedding

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "sample"

def ingest_portfolio_items():
    """Reads portfolio items from JSON, embeds their text, and stores them in pgvector."""
    portfolio_file = DATA_DIR / "portfolio_items.json"
    
    if not portfolio_file.exists():
        print(f"❌ Could not find portfolio file at: {portfolio_file}")
        return

    with open(portfolio_file, "r", encoding="utf-8") as f:
        portfolio_items = json.load(f)

    conn = get_db_connection()
    cur = conn.cursor()

    count = 0
    for item in portfolio_items:
        doc_id = item.get("id") or f"doc_{count}"
        title = item.get("title", "")
        description = item.get("description", "")
        tech_stack = item.get("tech_stack", item.get("skills", []))
        
        # Build text string to embed
        content = f"Title: {title}\nDescription: {description}\nTechnologies: {', '.join(tech_stack)}"
        
        print(f"Generating embedding for: {title}...")
        vector = get_embedding(content)
        
        if not vector:
            print(f"⚠️ Skipping {doc_id} due to embedding failure.")
            continue

        # Insert or update in vector database
        cur.execute("""
            INSERT INTO portfolio_vectors (id, content, metadata, embedding)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE 
            SET content = EXCLUDED.content,
                metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding;
        """, (
            str(doc_id),
            content,
            json.dumps(item),
            vector
        ))
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✅ Successfully ingested and embedded {count} portfolio items into PostgreSQL.")

if __name__ == "__main__":
    ingest_portfolio_items()