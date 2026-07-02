from dotenv import load_dotenv
import os

# API values
API_BASE_URL: str = os.getenv("API_BASE_URL", "https://localhost:8000/")
API_TOKEN: str = os.getenv("API_TOKEN", "default")