
import os
from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    JSON,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector

from embeddings.image_embeddings import ImageEmbedder

load_dotenv()

Base = declarative_base()
_engine = None


class ImageRecord(Base):
    __tablename__ = "image_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=False)
    content = Column(Text)
    image_metadata = Column("metadata", JSON, nullable=False)
    embedding = Column(Vector(512), nullable=False)


def get_engine():
    global _engine

    if _engine is None:
        connection = os.getenv("DATABASE_URL")

        if not connection:
            raise ValueError("DATABASE_URL is missing from .env")

        _engine = create_engine(connection)

    return _engine


def get_image_store():
    engine = get_engine()

    # Enable pgvector and create our image table.
    with engine.begin() as connection:
        connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector")
        )

    Base.metadata.create_all(engine)

    return sessionmaker(bind=engine)


def save_image_documents(documents):
    SessionLocal = get_image_store()
    embedder = ImageEmbedder()
    saved_count = 0

    with SessionLocal() as session:
        for doc in documents:
            image_path = doc.metadata.get("image_path")

            if not image_path or not os.path.isfile(image_path):
                continue

            # Generate an actual image vector using CLIP.
            vector = embedder.embed_image(image_path)

            record = ImageRecord(
                image_path=image_path,
                content=doc.page_content,
                image_metadata=doc.metadata,
                embedding=vector,
            )

            session.add(record)
            saved_count += 1

        session.commit()

    return saved_count


def search_images(query, k=3):
    SessionLocal = get_image_store()
    embedder = ImageEmbedder()

    # Convert the text query into a CLIP vector.
    query_vector = embedder.embed_query(query)

    with SessionLocal() as session:
        distance = ImageRecord.embedding.cosine_distance(query_vector)

        results = (
            session.query(ImageRecord, distance.label("distance"))
            .order_by(distance)
            .limit(k)
            .all()
        )

        return [
            {
                "image_path": record.image_path,
                "content": record.content,
                "metadata": record.image_metadata,
                "distance": score,
            }
            for record, score in results
        ]
