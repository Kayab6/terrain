import torch
from transformers import pipeline
from PIL import Image
import numpy as np
import io

class DepthEstimator:
    def __init__(self):
        print("Initializing DepthEstimator...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Use depth-anything-small for fast download and CPU-friendly inference
        self.pipe = pipeline(
            task="depth-estimation",
            model="depth-anything/Depth-Anything-V2-Small-hf",
            device=self.device,
        )
        print("DepthEstimator initialized.")

    def generate_depth_map(self, image_bytes: bytes) -> np.ndarray:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Resize large images for speed
        max_size = 512
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.LANCZOS)

        result = self.pipe(image)
        depth = result["depth"]  # PIL Image

        # Convert to numpy and normalize to 0–255
        depth_np = np.array(depth).astype(np.float32)
        d_min, d_max = depth_np.min(), depth_np.max()
        if d_max - d_min > 0:
            depth_norm = ((depth_np - d_min) / (d_max - d_min) * 255.0).astype(np.uint8)
        else:
            depth_norm = np.zeros_like(depth_np, dtype=np.uint8)

        return depth_norm


# Lazy singleton
depth_estimator = None

def get_depth_estimator():
    global depth_estimator
    if depth_estimator is None:
        depth_estimator = DepthEstimator()
    return depth_estimator
