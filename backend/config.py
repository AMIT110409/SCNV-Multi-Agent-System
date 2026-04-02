import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "SCNV Agent APIs"
    API_V1_STR = "/api/v1"
    
    # Optional Third-Party Toggles
    CELONIS_ENABLED = os.getenv("CELONIS_ENABLED", "false").lower() == "true"
    
    # LLM configurations
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
    
    # PostgreSQL memory layer
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/scnv")

settings = Settings()
