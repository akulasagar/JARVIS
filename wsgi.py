# WSGI entry point for deployment
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from webapp import app

if __name__ == "__main__":
    app.run() 