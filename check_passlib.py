from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hash = pwd_context.hash("admin123")
print(f"Hash: {hash}")

verify = pwd_context.verify("admin123", hash)
print(f"Verify: {verify}")
