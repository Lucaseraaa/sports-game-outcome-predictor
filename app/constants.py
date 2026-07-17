from dotenv import load_dotenv
import os

load_dotenv()

# API values
API_BASE_URL: str = os.getenv("API_BASE_URL", "https://localhost:8000/")
API_TOKEN: str = os.getenv("API_TOKEN", "default")
LEAGUE_ID: int = int(os.getenv("LEAGUE_ID", "0")) # Id della lega 'Serie A'