from dotenv import load_dotenv
import os

load_dotenv()

TOGETHER_API_KEY = os.getenv("API")

print(TOGETHER_API_KEY)
