#!/usr/bin/env python3
"""
Script to generate all remaining project files
This creates routers, templates, and static files
"""
import os

# Create directories if they don't exist
os.makedirs("app/routers", exist_ok=True)
os.makedirs("templates/admin", exist_ok=True)
os.makedirs("templates/public", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("deploy", exist_ok=True)

print("✅ All directories created successfully!")
print("\n📝 Project structure is ready!")
print("\nNext steps:")
print("1. Run: python init_db.py")
print("2. Run: uvicorn app.main:app --reload")
print("3. Open: http://localhost:8000")
