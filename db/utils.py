"""
Generic helper functions called by page scripts
"""
import json
from pathlib import Path
import hashlib
import re
 
DATA_DIR = Path(__file__).parent / "data"

# ── File loader ────────────────────────────────────────────────────────
def load(filename):
    file_path = Path(DATA_DIR) / filename
    if file_path.is_file():
        with open(file_path) as f:
            return json.load(f)
    else:
        print (f"Error: {file_path} does not exit")

def pseudonymise(email: str) -> str:
    """One-way hash so the raw address is never stored."""
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()

def mask_email(email: str) -> str:
    """Masks an email address so the raw value is not displayed."""
    local, _, domain = email.partition("@")
    return f"{local[0]}***@{domain}"

def mask_name(name: str) -> str:
    """Masks names by keeping only the first character of each word.
    
    Example: 'Jane Doe' -> 'J*** D***'
    """
    if not name or not isinstance(name, str):
        return name
    return re.sub(r'\b(\w)\w+', r'\1***', name)
