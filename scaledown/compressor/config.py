import os
from typing import Optional

# Global configuration state
_API_KEY: Optional[str] = os.environ.get("SCALEDOWN_API_KEY")

default_scaledown_api = "https://api.scaledown.xyz"

def set_api_key(api_key: Optional[str]) -> None:
    """Sets the global API key for ScaleDown."""
    global _API_KEY
    _API_KEY = api_key

def get_api_key() -> Optional[str]:
    """Retrieves the global API key."""
    return _API_KEY

def get_api_url() -> str:
    """Get ScaleDown API URL from environment or default."""
    return os.getenv("SCALEDOWN_API_URL", default_scaledown_api)
