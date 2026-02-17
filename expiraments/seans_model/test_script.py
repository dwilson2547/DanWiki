import torch
from transformers import AutoModel, AutoProcessor
from transformers.image_utils import load_image

modality = "image"
# Load model
model_name_or_path = "nvidia/llama-nemotron-embed-vl-1b-v2"

device = "cuda" if torch.cuda.is_available() else "cpu"

model = AutoModel.from_pretrained(
    model_name_or_path,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
    attn_implementation="flash_attention_2",
    device_map="auto"
).eval()


# Set max number of tokens (p_max_length) based on modality
if modality == "image":
    p_max_length = 2048
elif modality == "image_text":
    p_max_length = 10240
elif modality == "text":
    p_max_length = 8192
model.processor.p_max_length = p_max_length
# Sets max number of tiles an image can be split. Each tile consumes 256 tokens.
model.processor.max_input_tiles = 6
# Enables an extra tile with the full image at lower resolution
model.processor.use_thumbnail = True


# Example usage: single query with multiple image documents
query = "How is AI improving the intelligence and capabilities of robots?"
image_paths = [
    "https://developer.download.nvidia.com/images/isaac/nvidia-isaac-lab-1920x1080.jpg",
    "https://blogs.nvidia.com/wp-content/uploads/2018/01/automotive-key-visual-corp-blog-level4-av-og-1280x680-1.png",
    "https://developer-blogs.nvidia.com/wp-content/uploads/2025/02/hc-press-evo2-nim-25-featured-b.jpg"
]

# Load all images (load_image handles both local paths and URLs)
images = [load_image(img_path) for img_path in image_paths]

# Text descriptions corresponding to each image/document (used in image_text and text modalities)
document_texts = [
    "AI enables robots to perceive, plan, and act autonomously.",
    "AI is transforming autonomous vehicles by enabling safer, smarter, and more reliable decision-making on the road.",
    "A biological foundation model designed to analyze and generate DNA, RNA, and protein sequences."
]

# Run inference (common for all modalities)
with torch.inference_mode():
    queries_embeddings = model.encode_queries([query])
    
    if modality == "image_text":
        documents_embeddings = model.encode_documents(images=images, texts=document_texts)
    elif modality == "image":
        documents_embeddings = model.encode_documents(images=images)
    elif modality == "text":
        documents_embeddings = model.encode_documents(texts=document_texts)

def _l2_normalize(x: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    return x / (x.norm(p=2, dim=-1, keepdim=True) + eps)      

# Computes cosine similarity (as they are already normalized) between the query embeddings and the document embeddings
cos_sim = _l2_normalize(queries_embeddings) @ _l2_normalize(documents_embeddings).T

# Flatten logits to 1D array (handle both [batch_size] and [batch_size, 1] shapes)
cos_sim_flat = cos_sim.flatten()
    
# Get sorted indices (highest to lowest)
sorted_indices = torch.argsort(cos_sim_flat, descending=True)

print(f"\nQuery: {query}\n")
print(f"\nRanking (highest to lowest relevance for the modality {modality}):")
for rank, idx in enumerate(sorted_indices, 1):
    doc_idx = idx.item()
    sim_val = cos_sim_flat[doc_idx].item()
    if modality == "text":
        print(f"  Rank {rank}: cos_sim={sim_val:.4f} | Text: {document_texts[doc_idx]}")
    else:  # image or image_text modality
        print(f"  Rank {rank}: cos_sim={sim_val:.4f} | Image: {image_paths[doc_idx]}")