import os
import sys
import json
import csv
import glob
from pathlib import Path
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

# Load env
load_dotenv()

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = BASE_DIR / "hugo_data_samples"

# Initialize Firebase
cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', 'hugo-ai-credentials.json')
db_url = os.getenv('FIREBASE_DATABASE_URL')

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': db_url
    })

def _read_csv(path: Path) -> list:
    """Read CSV into list of dicts"""
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def _read_text(path: Path) -> str:
    with open(path, mode='r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def upload_all():
    print(f"Scanning {SAMPLES_DIR}...")
    
    # 1. Scan ALL CSV files
    csv_data = {}
    csv_files = list(SAMPLES_DIR.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files.")
    
    for p in csv_files:
        key = p.name.replace('.', '_') # Sanitize key
        print(f"Processing {p.name} -> {key}")
        csv_data[key] = _read_csv(p)

    # 2. Scan Emails
    emails_dir = SAMPLES_DIR / "emails"
    emails_data = {}
    if emails_dir.exists():
        email_files = list(emails_dir.glob("*.eml")) + list(emails_dir.glob("*.txt"))
        print(f"Found {len(email_files)} email files.")
        for p in email_files:
            key = p.name.replace('.', '_')
            emails_data[key] = _read_text(p)
    
    # 3. Specs Manifest (unchanged logic)
    specs_manifest = []
    specs_dir = SAMPLES_DIR / "specs"
    if specs_dir.exists():
        for p in specs_dir.glob("*.pdf"):
            specs_manifest.append({
                "filename": p.name,
                "size": p.stat().st_size
            })

    # Construct Payload
    payload = {
        "source": "hugo_data_samples_enriched",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "csv": csv_data,
        "emails": emails_data,
        "specs_manifest": specs_manifest
    }

    # Upload
    print("Uploading to Firebase...")
    ref = db.reference("hugo_data_samples")
    ref.set(payload)
    print("✅ Upload Success!")

if __name__ == "__main__":
    upload_all()
