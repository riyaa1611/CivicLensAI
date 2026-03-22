"""Shim: re-exports from scaledown.compressor.config for top-level access."""
from scaledown.compressor.config import get_api_key, set_api_key, get_api_url, default_scaledown_api

__all__ = ["get_api_key", "set_api_key", "get_api_url", "default_scaledown_api"]
