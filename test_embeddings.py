#test for text embeddings

from dotenv import load_dotenv
from embeddings.text_embeddings import get_text_embeddings

load_dotenv()

embeddings = get_text_embeddings()

text = "The company provides employee health insurance."

vector = embeddings.embed_query(text)

print("Vector length:", len(vector))
print("First 5 values:", vector[:5])



#test for image embeddings 


from pathlib import Path
from embeddings.image_embeddings import ImageEmbedder

# Find an image in the data folder
image_files = []

for extension in ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff"]:
    image_files.extend(Path("data").rglob(extension))

if not image_files:
    print("No images found in the data folder.")
else:
    image_path = image_files[0]
    print("Testing image:", image_path)

    embedder = ImageEmbedder()

    # Generate an image vector
    image_vector = embedder.embed_image(str(image_path))
    print("Image vector length:", len(image_vector))
    print("First 5 values:", image_vector[:5])

    # Generate a text query vector
    query_vector = embedder.embed_query("A financial report")

    print("Query vector length:", len(query_vector))
    print("First 5 values:", query_vector[:5])
