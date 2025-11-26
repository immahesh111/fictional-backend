try:
    print("Importing main...")
    from main import app
    print("Main imported successfully")
except Exception:
    import traceback
    traceback.print_exc()
