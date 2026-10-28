import torch
import open_clip
from PIL import Image


class ImageEmbedder:
    def __init__(self):
        self.model, _, self.preprocess = (
            open_clip.create_model_and_transforms(
                "ViT-B-32",
                pretrained="laion2b_s34b_b79k",
            )
        )

        self.model.eval()

    def embed_image(self, image_path):
        image = Image.open(image_path).convert("RGB")
        image_tensor = self.preprocess(image).unsqueeze(0)

        with torch.no_grad():
            vector = self.model.encode_image(image_tensor)
            vector = vector / vector.norm(
                dim=-1, keepdim=True
            )

        return vector[0].cpu().tolist()

    def embed_query(self, query):
        tokenizer = open_clip.get_tokenizer("ViT-B-32")
        tokens = tokenizer([query])

        with torch.no_grad():
            vector = self.model.encode_text(tokens)
            vector = vector / vector.norm(
                dim=-1, keepdim=True
            )

        return vector[0].cpu().tolist()

