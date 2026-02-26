"""
Hardware-based model selection for Whisper ASR.

Resolves model and compute_type based on available GPU VRAM or explicit preset.
Supports: tiny, base, small, medium, large-v3, large-v3-turbo.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# VRAM requirements (MB) for float16, int8
# Source: faster-whisper docs, SYSTRAN/faster-whisper
MODEL_PRESETS = {
    "tiny": {"model": "tiny", "compute_type": "float16", "vram_mb": 1000},
    "base": {"model": "base", "compute_type": "float16", "vram_mb": 1000},
    "small": {"model": "small", "compute_type": "float16", "vram_mb": 2000},
    "medium": {"model": "medium", "compute_type": "float16", "vram_mb": 5000},
    "large-v3": {"model": "large-v3", "compute_type": "float16", "vram_mb": 10000},
    "large-v3-turbo": {"model": "large-v3-turbo", "compute_type": "float16", "vram_mb": 3000},
    # int8 variants for low VRAM
    "large-v3-int8": {"model": "large-v3", "compute_type": "int8", "vram_mb": 6000},
    "medium-int8": {"model": "medium", "compute_type": "int8", "vram_mb": 3000},
}


def get_gpu_vram_mb() -> Optional[int]:
    """Get available GPU VRAM in MB. Returns None if no GPU."""
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return mem_info.total // (1024 * 1024)
    except Exception as e:
        logger.debug(f"GPU VRAM detection failed: {e}")
        return None


def resolve_model_for_hardware(
    model_preset: str = "auto",
    device: str = "cuda",
) -> Tuple[str, str]:
    """
    Resolve model name and compute_type based on available hardware.

    Args:
        model_preset: "auto" | "tiny" | "base" | "small" | "medium" | "large-v3" | "large-v3-turbo"
        device: "cuda" or "cpu"

    Returns:
        (model_name, compute_type)
    """
    if model_preset != "auto" and model_preset in MODEL_PRESETS:
        preset = MODEL_PRESETS[model_preset]
        return preset["model"], preset["compute_type"]

    if model_preset == "auto" and device == "cuda":
        vram_mb = get_gpu_vram_mb()
        if vram_mb:
            # Select best model for available VRAM
            if vram_mb >= 10000:
                return "large-v3", "float16"
            if vram_mb >= 6000:
                return "large-v3", "int8"
            if vram_mb >= 5000:
                return "medium", "float16"
            if vram_mb >= 3000:
                return "large-v3-turbo", "float16"
            if vram_mb >= 2000:
                return "small", "float16"
            if vram_mb >= 1000:
                return "base", "float16"
            return "tiny", "float16"
        logger.warning("GPU VRAM detection failed, using medium model")
        return "medium", "float16"

    if device == "cpu":
        return "base", "int8"

    return "large-v3", "float16"
