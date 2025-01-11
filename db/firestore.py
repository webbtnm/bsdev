import os
from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()

# Use credentials from the .env file
credentials_path = os.getenv("FIRESTORE_CREDENTIALS")
firestore_client = firestore.Client.from_service_account_json(credentials_path)

db = firestore_client
