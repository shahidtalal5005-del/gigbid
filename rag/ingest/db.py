import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "gigbid")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def init_db():
    """Ensure pgvector extension exists and create the document vector table."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Enable pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # 2. Create vector store table for 768-dim nomic-embed-text vectors
        cur.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_vectors (
                id VARCHAR(255) PRIMARY KEY,
                content TEXT NOT NULL,
                metadata JSONB,
                embedding vector(768)
            );
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized successfully with pgvector extension and portfolio_vectors table.")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

if __name__ == "__main__":
    init_db()