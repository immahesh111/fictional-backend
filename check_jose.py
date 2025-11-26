try:
    from jose import jwt
    print(f"python-jose version: {jwt.__file__}")
    print("Successfully imported jose.jwt")
    
    token = jwt.encode({"sub": "test"}, "secret", algorithm="HS256")
    print(f"Token: {token}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
