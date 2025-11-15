"""
Dynamic Watermark Embedder for AEGIS Live Feed
Embeds HMAC-SHA256 based tokens into video frames for liveness detection
"""

import cv2
import numpy as np
import time
import hmac
import hashlib
from datetime import datetime
import threading

# Server secret key for HMAC generation
SERVER_SECRET_KEY = b"YourUnbreakableWatermarkSecretKey12345"

# Visibility settings
VISIBILITY_FLIP_INTERVAL_SECONDS = 10


def generate_hmac_token():
    """
    Generates a unique 4-digit token based on HMAC-SHA256.
    Changes every second, ensuring non-sequential jumps.
    
    Returns:
        str: 4-digit token (0000-9999)
    """
    current_time_seconds = int(time.time())
    message = str(current_time_seconds).encode('utf-8')
    
    # Compute HMAC-SHA256
    hmac_digest = hmac.new(
        key=SERVER_SECRET_KEY,
        msg=message,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Truncate to last 4 hex digits and convert to 4-digit decimal
    last_4_hex = hmac_digest[-4:]
    token_int = int(last_4_hex, 16)
    final_token = token_int % 10000
    
    return f"{final_token:04d}"


def get_current_opacity():
    """
    Determines current watermark opacity for adaptive visibility.
    Alternates between high (1.0) and low (0.2) every 10 seconds.
    
    Returns:
        float: Opacity multiplier (0.2 or 1.0)
    """
    current_time_seconds = int(time.time())
    
    if current_time_seconds % (VISIBILITY_FLIP_INTERVAL_SECONDS * 2) < VISIBILITY_FLIP_INTERVAL_SECONDS:
        return 1.0  # High opacity
    else:
        return 0.2  # Low opacity


def generate_watermark_text():
    """
    Creates the complete dynamic watermark signature.
    Format: TST-H:<4-digit-token> | T:<timestamp>
    
    Returns:
        str: Watermark text to embed
    """
    token = generate_hmac_token()
    dt_now = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    signature = f"TST-H:{token} | T:{dt_now}"
    return signature


def embed_watermark(frame, watermark_text=None, opacity_multiplier=None):
    """
    Embeds dynamic watermark onto video frame.
    Includes semi-transparent background rectangle for contrast.
    
    Args:
        frame: OpenCV frame (BGR format)
        watermark_text: Custom watermark text (auto-generated if None)
        opacity_multiplier: Alpha value for visibility (auto-calculated if None)
    
    Returns:
        np.ndarray: Frame with embedded watermark
    """
    if frame is None:
        return None
    
    # Auto-generate watermark text if not provided
    if watermark_text is None:
        watermark_text = generate_watermark_text()
    
    # Auto-calculate opacity if not provided
    if opacity_multiplier is None:
        opacity_multiplier = get_current_opacity()
    
    H, W = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_thickness = 2
    
    # Calculate text size
    text_size = cv2.getTextSize(watermark_text, font, font_scale, font_thickness)[0]
    text_width, text_height = text_size[0], text_size[1]
    
    padding = 10
    text_x = W - text_width - padding
    text_y = H - padding
    
    # Draw semi-transparent background rectangle
    overlay = frame.copy()
    rect_color = (0, 0, 0)
    rect_alpha = 0.4 * opacity_multiplier
    
    rect_top_left_x = text_x - padding
    rect_top_left_y = text_y - text_height - padding
    rect_bottom_right_x = W
    rect_bottom_right_y = H
    
    cv2.rectangle(
        overlay,
        (rect_top_left_x, rect_top_left_y),
        (rect_bottom_right_x, rect_bottom_right_y),
        rect_color,
        -1
    )
    
    cv2.addWeighted(overlay, rect_alpha, frame, 1 - rect_alpha, 0, frame)
    
    # Draw watermark text
    text_opacity = opacity_multiplier
    if text_opacity < 1.0:
        text_color = (150, 150, 150)  # Gray when faint
    else:
        text_color = (0, 255, 255)  # Cyan when visible
    
    cv2.putText(
        frame,
        watermark_text,
        (text_x, text_y),
        font,
        font_scale,
        text_color,
        font_thickness,
        cv2.LINE_AA
    )
    
    return frame


class WatermarkEmbedder:
    """
    Thread-safe watermark embedder for continuous frame processing.
    Caches watermark text to ensure same token within a second.
    """
    
    def __init__(self, server_secret_key=None):
        """Initialize embedder with optional custom secret key."""
        global SERVER_SECRET_KEY
        if server_secret_key:
            SERVER_SECRET_KEY = server_secret_key
        
        self.last_watermark_text = None
        self.last_watermark_time = 0
        self.lock = threading.Lock()
    
    def get_watermark_text(self):
        """
        Get cached watermark text or generate new one.
        Ensures same token is used for all frames within 1 second.
        
        Returns:
            str: Watermark text
        """
        with self.lock:
            current_time = int(time.time())
            
            # Regenerate if time changed
            if current_time != self.last_watermark_time:
                self.last_watermark_text = generate_watermark_text()
                self.last_watermark_time = current_time
            
            return self.last_watermark_text
    
    def embed(self, frame):
        """
        Embed watermark into frame with cached text.
        
        Args:
            frame: OpenCV frame
        
        Returns:
            np.ndarray: Frame with watermark
        """
        if frame is None:
            return None
        
        watermark_text = self.get_watermark_text()
        opacity_multiplier = get_current_opacity()
        
        return embed_watermark(frame, watermark_text, opacity_multiplier)


# Global singleton instance
_embedder = None
_embedder_lock = threading.Lock()


def get_watermark_embedder():
    """
    Get or create global watermark embedder instance (singleton).
    Thread-safe initialization.
    
    Returns:
        WatermarkEmbedder: Global embedder instance
    """
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                _embedder = WatermarkEmbedder()
    return _embedder
