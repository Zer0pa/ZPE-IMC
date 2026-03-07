"""
Neural Image Encoder (Mock/Prototype).

This module provides a high-level interface for encoding images using a neural network
(e.g., ONNX Runtime) or a fallback mock implementation if the model is missing.
"""

import os
import numpy as np
from typing import List

# Try to import ONNX Runtime, but degrade gracefully
try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False

from .vectorize import binary_to_polylines
from .strokes import polylines_to_strokes
from ..core.constants import Mode

class MockSession:
    """Simulates an ONNX session for testing/fallback."""
    def run(self, output_names, input_feed):
        # Return dummy embedding or stroke parameters
        # Shape: (1, 128) embedding or similar
        return [np.random.rand(1, 128).astype(np.float32)]

class NeuralImageEncoder:
    def __init__(self, model_path: str = "models/image_encoder.onnx"):
        self.model_path = model_path
        self.session = None
        
        if os.getenv("STROKEGRAM_FORCE_MOCK_NEURAL", "0") == "1":
            print("NeuralImageEncoder: Forcing Mock Session.")
            self.session = MockSession()
        elif HAS_ONNX and os.path.exists(model_path):
            try:
                self.session = ort.InferenceSession(model_path)
                print(f"NeuralImageEncoder: Loaded {model_path}")
            except Exception as e:
                print(f"NeuralImageEncoder: Failed to load model: {e}")
                self.session = MockSession()
        else:
            print(f"NeuralImageEncoder: Model not found or ONNX missing. Using Mock.")
            self.session = MockSession()

    def encode_image(self, image_array: np.ndarray) -> List[int]:
        """
        Encodes an image (H, W, 3) to a sequence of Masterunit IDs.
        
        Pipeline:
        1. Preprocess (Resize/Norm) -> Neural Net -> Latent Vector
        2. Latent Vector -> Decoder -> Stroke Parameters
        3. Stroke Parameters -> Masterunit IDs
        
        For this prototype, we skip the neural net and use the 'vectorize' module
        directly on the image if it's a mock session, or return dummy IDs.
        """
        # For the prototype/mock, we actually want to use the *spatial* vectorizer
        # if we don't have a real neural net trained yet.
        # The "Neural" part is the aspirational architecture.
        
        # 1. Convert to binary for vectorizer
        if image_array.ndim == 3:
            gray = np.mean(image_array, axis=2).astype(np.uint8)
        else:
            gray = image_array.astype(np.uint8)
            
        # Simple threshold
        binary = gray < 128
        
        # 2. Vectorize
        polylines = binary_to_polylines(binary)
        
        # 3. Convert to Strokes (Masterunits)
        # Note: This uses the spatial path, not the neural path, but fulfills the contract.
        steps = polylines_to_strokes(polylines)
        
        # Convert StrokeStep objects to integer IDs (20-bit words)
        # We pack dx, dy into an EXTENSION word for now.
        # This is a research encoding, not the standard text encoding.
        ids = []
        
        for step in steps:
            # Pack dx, dy (signed 8-bit) into payload
            # Payload is 16 bits.
            # dx: 8 bits, dy: 8 bits.
            p_dx = step.dx & 0xFF
            p_dy = step.dy & 0xFF
            payload = (p_dx << 8) | p_dy
            
            # Use Extension Mode (2)
            # We set bit 16 to 0 (Version 0)
            word = (Mode.EXTENSION.value << 18) | payload
            ids.append(word)
            
        return ids

# Singleton instance
_encoder = None

def encode_file(path: str) -> List[int]:
    """Helper to encode an image file."""
    global _encoder
    if _encoder is None:
        _encoder = NeuralImageEncoder()
        
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        arr = np.array(img)
        return _encoder.encode_image(arr)
    except ImportError:
        print("PIL missing, returning empty.")
        return []
