#!/usr/bin/env python3
"""
Pharma Navigator - Colab Setup Script
Runs in Google Colab to set up the RAG system and start Chainlit
"""

# Google Colab setup
import os
import subprocess
import sys

print("=" * 60)
print("🚀 Pharma Navigator - Google Colab Setup")
print("=" * 60)

# Step 1: Check Python version
python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
print(f"\n✅ Python version: {python_version}")

# Step 2: Install requirements
print("\n📦 Installing dependencies...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"], 
               cwd="/content/pharma-navigator")

# Step 3: Verify database
print("\n🗄️ Checking FAISS database...")
db_path = "/content/pharma-navigator/faiss_db"
if os.path.exists(f"{db_path}/faiss.index"):
    print(f"✅ FAISS database found at {db_path}")
else:
    print(f"⚠️ Database not found. Will need to ingest PDFs.")

# Step 4: Start Chainlit
print("\n🔥 Starting Chainlit server...")
print("📍 Server will be available at http://localhost:8000")
print("💡 Use ngrok or Colab tunnel to access from browser")
print("\n" + "=" * 60)

os.chdir("/content/pharma-navigator")
os.system("python3 -m chainlit run src/app.py -h --host 0.0.0.0 --port 8000")
