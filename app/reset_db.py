import os

db_file = "sql_app.db"

if os.path.exists(db_file):
    try:
        os.remove(db_file)
        print("✅ SUCCESS: Old database deleted!")
        print("🚀 Restart your server now to build the new one.")
    except Exception as e:
        print(f"❌ Error: Could not delete. Close VS Code and try again. {e}")
else:
    print("⚠️ No database found. You are already clean!")