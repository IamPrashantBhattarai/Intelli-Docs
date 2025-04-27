import os
import torch
import clip
import faiss
import pickle
import numpy as np
import requests
import io
from PIL import Image

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# Device Configuration
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load CLIP Model
model, preprocess = clip.load("ViT-B/16", device=device)

# Load fine-tuned weights
model.load_state_dict(torch.load("C:\\Users\\Roshan Chaudhary\\Desktop\\major project\\clip_finetuned\\clip_finetuned.pth", map_location=device))
model.eval()

EMBEDDINGS_CACHE_FILE = "embeddings_cache.pkl"

def load_existing_embeddings(cache_file):
    """Load cached embeddings from a file."""
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            data = pickle.load(f)
        return data
    return {}

def save_embeddings(cache_file, embedding_dict):
    """Save the embeddings dictionary to disk."""
    with open(cache_file, 'wb') as f:
        pickle.dump(embedding_dict, f)

def fetch_cloudinary_images():
    """
    Fetches all images from Cloudinary and returns a dictionary:
    {public_id: image_url}
    """
    import cloudinary
    import cloudinary.api

    cloudinary.config(
    cloud_name="dyq7iqdyc", 
    api_key="775973687362869",
    api_secret="wuPwai-7yG2hVXqFLgNvFR03iKc"   
)

    images = {}
    result = cloudinary.api.resources(type="upload", max_results=500)
    for img in result.get("resources", []):
        images[img["public_id"]] = img["secure_url"]
    return images

def update_embeddings(cloudinary_images, embedding_dict):
    """
    Fetches images from Cloudinary, processes them, and stores embeddings.
    """
    for public_id, url in cloudinary_images.items():
        if url in embedding_dict:  # Skip already processed images
            continue
        try:
            response = requests.get(url)
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
            image_input = preprocess(image).unsqueeze(0).to(device)
        except Exception as e:
            continue
        with torch.no_grad():
            image_embedding = model.encode_image(image_input)
            image_embedding /= image_embedding.norm(dim=-1, keepdim=True)
        embedding_dict[url] = image_embedding.cpu()
    return embedding_dict

def build_faiss_index(embedding_dict):
    """Builds a FAISS index from the stored embeddings."""
    image_urls = list(embedding_dict.keys())
    if len(image_urls) == 0:
        return None, []
    
    embeddings = torch.cat([embedding_dict[url] for url in image_urls], dim=0).numpy().astype("float32")
    d = embeddings.shape[1]
    
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)
    
    return index, image_urls

def query_index(query, index, image_urls, k=3):
    """Finds top k matching images using FAISS."""
    text_tokens = clip.tokenize([query]).to(device)
    with torch.no_grad():
        text_embedding = model.encode_text(text_tokens)
        text_embedding /= text_embedding.norm(dim=-1, keepdim=True)
    
    query_vector = text_embedding.cpu().numpy().astype("float32")
    distances, indices = index.search(query_vector, k)
    
    top_image_urls = [image_urls[i] for i in indices[0]]
    return top_image_urls

def image_retrieval(query, top_k=3):
    """
    Retrieves the top-k most relevant image URLs based on the given text query.
    
    :param query: Text query describing the image.
    :param top_k: Number of images to retrieve.
    :return: List of image URLs.
    """
    embeddings_dict = load_existing_embeddings(EMBEDDINGS_CACHE_FILE)
    cloudinary_images = fetch_cloudinary_images()
    embeddings_dict = update_embeddings(cloudinary_images, embeddings_dict)
    save_embeddings(EMBEDDINGS_CACHE_FILE, embeddings_dict)

    index, image_urls = build_faiss_index(embeddings_dict)
    if index is None:
        return []

    return query_index(query, index, image_urls, top_k)


if __name__ == "__main__":
    query_text = "give me a image with stone"
    results = image_retrieval(query_text, top_k=3)

    print("🔹 Top matching image URLs:")
    for url in results:
        print(url)
