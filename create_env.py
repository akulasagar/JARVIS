#!/usr/bin/env python3
"""
Script to create .env file with proper encoding
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write("GEMINI_API_KEY=AIzaSyDSk4ejEc1hP4w6ToYWtpw5nzt6Ej_FsiM\n")
    f.write("SECRET_KEY=dec8752d10de7dddc9f1e2119dcaf6c71b5bca84096508dcf390f49152a34fee\n")

print("✅ .env file created successfully!")
print("📝 Contents:")
with open('.env', 'r', encoding='utf-8') as f:
    print(f.read()) 