import os, dotenv

env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
dotenv.load_dotenv(env_file, override=True)

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")