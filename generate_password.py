#!/usr/bin/env python3
"""Script zum Generieren eines Passwort-Hashes für HTTP Basic Auth"""
from werkzeug.security import generate_password_hash
import sys

if len(sys.argv) < 2:
    print("Usage: python3 generate_password.py <dein_passwort>")
    sys.exit(1)

password = sys.argv[1]
hash_value = generate_password_hash(password)
print(f"\nPasswort-Hash für '{password}':")
print(hash_value)
print("\nFüge das in docker-compose.yml als AUTH_PASSWORD_HASH ein")
