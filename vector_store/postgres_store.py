import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from embeddings.text_embeddings import get_text_embeddings

load_dotenv()

def get_text_store():
    connection = os.getenv("DATABASE_URL")

    if not connection:
        raise ValueError("DATABASE_URL is missing from .env")

    return PGVector(
        embeddings=get_text_embeddings(),
        collection_name="text_documents",
        connection=connection,
        use_jsonb=True,
    )

from sqlalchemy import create_engine, text

def delete_documents_by_source(source_name: str) -> int:
    """Delete existing embeddings for a source file so re-ingestion does not leave duplicate or stale chunks."""
    connection = os.getenv("DATABASE_URL")
    if not connection:
        return 0

    engine = create_engine(connection)
    sql = text("""
        DELETE FROM langchain_pg_embedding
        WHERE collection_id IN (
            SELECT uuid FROM langchain_pg_collection WHERE name = 'text_documents'
        )
        AND cmetadata->>'source' = :source_name
    """)

    with engine.begin() as conn:
        res = conn.execute(sql, {"source_name": source_name})
        return res.rowcount