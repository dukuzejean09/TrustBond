"""
Evidence analysis module for computing image quality metrics.
Computes blur detection, tamper detection, and perceptual hashing.
"""
import hashlib
import io
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import numpy as np

# Lazy imports to avoid dependency errors if packages not installed
Image = None
cv2 = None
np = None


def _import_dependencies():
    """Lazy import of image processing dependencies."""
    global Image, cv2, np
    if Image is None:
        try:
            from PIL import Image
        except ImportError:
            Image = None
    if cv2 is None:
        try:
            import cv2
        except ImportError:
            cv2 = None
    if np is None:
        try:
            import numpy as np
        except ImportError:
            np = None


def compute_image_metrics(image_data: bytes) -> Dict[str, Any]:
    """
    Compute blur_score, tamper_score, and perceptual_hash for image evidence.
    
    Returns:
        Dict with blur_score (0-1, lower is more blurred), 
        tamper_score (0-1, higher means more suspicious),
        perceptual_hash (hex string),
        quality_label (good/fair/poor),
        ai_checked_at (timestamp)
    """
    _import_dependencies()
    
    result = {
        "blur_score": None,
        "tamper_score": None,
        "perceptual_hash": None,
        "quality_label": "fair",
        "ai_checked_at": datetime.now(timezone.utc),
    }
    
    if Image is None or cv2 is None or np is None:
        # Fallback: compute simple hash if dependencies not available
        result["perceptual_hash"] = hashlib.sha256(image_data).hexdigest()
        return result
    
    try:
        # Load image from bytes
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to numpy for OpenCV processing
        img_array = np.array(image)
        
        # Convert to grayscale for analysis
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # 1. Compute blur score using Laplacian variance
        # Higher variance = sharper image, lower variance = more blurred
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize to 0-1 scale (higher = sharper)
        # Typical variance ranges from 0 to 1000+
        blur_score = min(1.0, laplacian_var / 500.0)
        result["blur_score"] = round(blur_score, 3)
        
        # 2. Compute tamper score using edge analysis and noise patterns
        # tampered images often have inconsistent edge patterns
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Analyze noise patterns (tampering often leaves inconsistent noise)
        noise_estimate = _estimate_noise(gray)
        
        # Combine metrics for tamper score
        # Low edge density + abnormal noise = more suspicious
        tamper_score = 0.5
        if edge_density < 0.05:
            tamper_score += 0.2  # Unusually low edge density
        if noise_estimate > 0.3:
            tamper_score += 0.2  # Abnormal noise patterns
        if noise_estimate < 0.01:
            tamper_score += 0.1  # Too clean (possible over-processing)
        
        result["tamper_score"] = round(min(1.0, tamper_score), 3)
        
        # 3. Compute perceptual hash (pHash-like)
        # Resize to 8x8, convert to grayscale, compute hash
        image_hash = _compute_perceptual_hash(gray)
        result["perceptual_hash"] = image_hash
        
        # 4. Determine quality label based on blur and tamper scores
        if result["blur_score"] is not None and result["tamper_score"] is not None:
            if result["blur_score"] >= 0.7 and result["tamper_score"] <= 0.3:
                result["quality_label"] = "good"
            elif result["blur_score"] <= 0.3 or result["tamper_score"] >= 0.7:
                result["quality_label"] = "poor"
            else:
                result["quality_label"] = "fair"
        
    except Exception as e:
        # Fallback on any processing error
        result["perceptual_hash"] = hashlib.sha256(image_data).hexdigest()
    
    return result


def _estimate_noise(gray_image) -> float:
    """Estimate noise level in grayscale image using high-frequency components."""
    if cv2 is None or np is None:
        return 0.15  # Default middle value
    
    try:
        # Use median blur to estimate noise
        median = cv2.medianBlur(gray_image, 5)
        noise = np.abs(gray_image.astype(float) - median.astype(float))
        noise_level = np.std(noise) / 255.0
        return min(1.0, noise_level * 10)  # Normalize to 0-1
    except Exception:
        return 0.15


def _compute_perceptual_hash(gray_image, size: int = 8) -> str:
    """Compute perceptual hash (average hash variant) for image."""
    if Image is None or np is None:
        # Fallback to SHA256 if PIL not available
        return hashlib.sha256(gray_image.tobytes() if hasattr(gray_image, 'tobytes') else str(gray_image).encode()).hexdigest()[:64]
    
    try:
        # Resize to size x size
        resized = Image.fromarray(gray_image).resize((size, size), Image.Resampling.LANCZOS)
        resized_array = np.array(resized)
        
        # Compute average and generate hash
        avg = resized_array.mean()
        bits = (resized_array > avg).astype(int)
        
        # Convert to hex string
        hash_str = ''.join(str(b) for b in bits.flatten())
        return hex(int(hash_str, 2))[2:].zfill(64)
    except Exception:
        return hashlib.sha256(gray_image.tobytes() if hasattr(gray_image, 'tobytes') else str(gray_image).encode()).hexdigest()[:64]


def analyze_evidence_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze an evidence file and return computed metrics.
    
    Args:
        file_path: Path to the evidence file
        
    Returns:
        Dict with computed metrics
    """
    try:
        with open(file_path, 'rb') as f:
            image_data = f.read()
        return compute_image_metrics(image_data)
    except Exception as e:
        return {
            "blur_score": None,
            "tamper_score": None,
            "perceptual_hash": None,
            "quality_label": "fair",
            "ai_checked_at": datetime.now(timezone.utc),
            "error": str(e),
        }


def is_likely_screenshot(image_data: bytes) -> Tuple[bool, float]:
    """
    Detect if an image is likely a screenshot based on characteristics.
    
    Returns:
        Tuple of (is_screenshot, confidence)
    """
    _import_dependencies()
    
    if Image is None or np is None:
        return False, 0.0
    
    try:
        image = Image.open(io.BytesIO(image_data))
        img_array = np.array(image)
        
        # Check for consistent solid color areas (common in screenshots)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Analyze color distribution - screenshots often have uniform colors
        unique_colors = len(np.unique(gray))
        
        # Screenshots typically have fewer unique values
        is_screenshot = unique_colors < 50
        confidence = min(1.0, (50 - unique_colors) / 50) if unique_colors < 50 else 0.0
        
        return is_screenshot, confidence
    except Exception:
        return False, 0.0


def is_likely_screen_recording(image_data: bytes) -> Tuple[bool, float]:
    """
    Detect if an image is from a screen recording.
    
    Returns:
        Tuple of (is_screen_recording, confidence)
    """
    # Screen recordings often have black borders or UI elements
    _import_dependencies()
    
    if Image is None or np is None:
        return False, 0.0
    
    try:
        image = Image.open(io.BytesIO(image_data))
        img_array = np.array(image)
        
        # Check for black borders
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        h, w = gray.shape
        
        # Check border regions for solid colors
        border_pixels = np.concatenate([
            gray[0, :],  # top
            gray[-1, :],  # bottom
            gray[:, 0],  # left
            gray[:, -1],  # right
        ])
        
        # If borders are mostly black (common in screen recordings)
        border_dark_ratio = np.mean(border_pixels < 30)
        
        is_recording = border_dark_ratio > 0.3
        confidence = border_dark_ratio if is_recording else 0.0
        
        return is_recording, min(1.0, confidence)
    except Exception:
        return False, 0.0