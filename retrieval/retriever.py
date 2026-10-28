
import os
import re

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from rank_bm25 import BM25Okapi
from vector_store.postgres_store import get_text_store

from retrieval.reranker import rerank_documents

load_dotenv()


# 1. Similarity search
def retrieve_similarity(query, k=3):
    """Find documents using embedding similarity."""

    store = get_text_store()

    documents = store.similarity_search(query, k=k)

    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
        }
        for doc in documents
    ]


# 2. Get all text documents from PostgreSQL
def get_all_text_documents():
    """Load documents from the LangChain PGVector collection."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is missing from .env")

    engine = create_engine(database_url)

    sql = text("""
        SELECT e.document, e.cmetadata
        FROM langchain_pg_embedding AS e
        JOIN langchain_pg_collection AS c
          ON e.collection_id = c.uuid
        WHERE c.name = :collection_name
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {"collection_name": "text_documents"},
        ).fetchall()

    return [
        {
            "content": row[0],
            "metadata": row[1] or {},
        }
        for row in rows
        if row[0]
    ]


# 3. BM25 keyword search
def retrieve_bm25(query, k=3):
    """Find documents using BM25 keyword ranking."""

    documents = get_all_text_documents()

    if not documents:
        return []

    # Convert each document into lowercase words
    tokenized_documents = [
        re.findall(r"\w+", doc["content"].lower())
        for doc in documents
    ]

    # Create the BM25 model
    bm25 = BM25Okapi(tokenized_documents)

    # Adjust zero or negative IDF values for small collections
    bm25.idf = {
        word: max(score, 0.1)
        for word, score in bm25.idf.items()
    }

    # Convert the query into lowercase words
    query_words = re.findall(r"\w+", query.lower())

    # Calculate scores
    scores = bm25.get_scores(query_words)

    # Sort documents by score, highest first
    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True,
    )

    results = []

    for index in ranked_indices:
        if scores[index] <= 0:
            continue

        results.append({
            **documents[index],
            "score": float(scores[index]),
        })

        if len(results) == k:
            break

    return results


# 4. Hybrid search
def retrieve_hybrid(query, k=15):
    """Combine similarity search and BM25 using Reciprocal Rank Fusion, ensuring all documents are covered."""

    # Get results from both search methods
    similarity_results = retrieve_similarity(query, k=k)
    bm25_results = retrieve_bm25(query, k=k)

    combined = {}

    # Combine rankings using Reciprocal Rank Fusion (RRF)
    for results in (similarity_results, bm25_results):

        for rank, item in enumerate(results, start=1):
            content = item["content"]

            if content not in combined:
                combined[content] = {
                    "content": content,
                    "metadata": item["metadata"],
                    "hybrid_score": 0.0,
                }

            # Higher-ranked results receive a larger contribution
            combined[content]["hybrid_score"] += 1 / (60 + rank)

    # Ensure all available document sources have candidate coverage
    all_docs = get_all_text_documents()
    sources_in_combined = {
        item["metadata"].get("source") for item in combined.values()
    }

    for doc in all_docs:
        source_name = doc["metadata"].get("source")
        if source_name and source_name not in sources_in_combined:
            content = doc["content"]
            if content not in combined:
                combined[content] = {
                    "content": content,
                    "metadata": doc["metadata"],
                    "hybrid_score": 0.001,
                }
                sources_in_combined.add(source_name)

    # Sort by combined score, highest first
    ranked_results = sorted(
        combined.values(),
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )

    return ranked_results


def retrieve_hybrid_reranked(query, k=20, top_n=6):

    candidates = retrieve_hybrid(query, k=k)

    print("\nQUESTION:", query)
    print("HYBRID CANDIDATE COUNT:", len(candidates))

    if not candidates:
        return []

    reranked_results = rerank_documents(
        query=query,
        documents=candidates,
        top_n=top_n
    )

    print("RERANKED RESULT COUNT:", len(reranked_results))

    return reranked_results