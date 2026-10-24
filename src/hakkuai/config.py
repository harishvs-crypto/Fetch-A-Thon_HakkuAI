"""
Configuration management for HakkuAI agent.
Handles environment variables, default settings, and path resolutions.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

class Settings:
    AGENT_NAME: str = os.getenv("HAKKUAI_AGENT_NAME", "hakkuai_welfare_assistant")
    AGENT_PORT: int = int(os.getenv("HAKKUAI_AGENT_PORT", "8000"))
    AGENT_SEED: str = os.getenv("HAKKUAI_AGENT_SEED", "hakkuai_secure_demo_seed_do_not_use_in_prod")
    MAILBOX_ENABLED: bool = os.getenv("HAKKUAI_MAILBOX_ENABLED", "false").lower() in ("true", "1", "yes")
    AGENTVERSE_API_KEY: str | None = os.getenv("AGENTVERSE_API_KEY", None)
    AGENTVERSE_MAILBOX_KEY: str | None = os.getenv("AGENTVERSE_MAILBOX_KEY", None)
    
    # Network Configuration (testnet / mainnet)
    AGENT_NETWORK: str = os.getenv("HAKKUAI_NETWORK", "testnet")
    
    # Path to scheme database JSON
    SCHEMES_FILE: Path = Path(os.getenv("SCHEMES_DATA_PATH", str(DATA_DIR / "schemes.json")))
    
    # Log Level
    LOG_LEVEL: str = os.getenv("AGENT_LOG_LEVEL", "INFO")
    
    # Emergency numbers for India
    EMERGENCY_NATIONAL_NUMBER: str = "112"
    EMERGENCY_AMBULANCE_NUMBER: str = "108"
    
    # Supported Languages
    SUPPORTED_LANGUAGES = ["en", "ta"]

settings = Settings()
