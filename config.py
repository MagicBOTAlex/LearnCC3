import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables (.env first, then .env.example if missing)
env_path = Path(".env")
env_example_path = Path(".env.example")

if env_path.is_file():
    load_dotenv(dotenv_path=env_path)
elif env_example_path.is_file():
    load_dotenv(dotenv_path=env_example_path)

# Retrieve MODEL from environment with default fallback
MODEL_NAME = os.getenv("MODEL", "gemma4:12b")

# Retrieve OUTPUT_PDF from environment with default fallback "out.pdf"
OUTPUT_PDF = os.getenv("OUTPUT_PDF", "out.pdf")

# Retrieve OUTPUT_FONT from environment with default fallback "Noto Sans Mono CJK HK"
OUTPUT_FONT = os.getenv("OUTPUT_FONT", "Noto Sans Mono CJK HK")

# Directory where local font files will be downloaded/stored
LIB_DIR = Path(__file__).parent / "lib"

# Retrieve SYSTEM PROMPT from environment, with typo fallback, or use default
DEFAULT_SYSTEM_PROMPT = "Translate to Simplified Chinese (Mandarin). Use common Chinese words so it is easy to read."
SYSTEM_PROMPT = os.getenv(
    "TRANSLATION_PROMPT", os.getenv("TRANSLATION_PROMT", DEFAULT_SYSTEM_PROMPT)
)

console = Console()
