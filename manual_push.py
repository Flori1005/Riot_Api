import requests
import json
import sys
import os
import glob
from datetime import datetime

# Import configuration
try:
    from config import N8N_WEBHOOK_URL
except ImportError:
    print("❌ Error: config.py not found.")
    print("   Please create 'config.py' with: N8N_WEBHOOK_URL = '...'")
    sys.exit(1)

def get_json_files():
    """Returns a list of JSON files in the current directory, sorted by modification time (newest first)."""
    json_files = glob.glob("*.json")
    if not json_files:
        return []
    
    # Sort by mtime, newest first
    json_files.sort(key=os.path.getmtime, reverse=True)
    return json_files

def format_timestamp(ts):
    """Formats a timestamp into a readable string."""
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def select_file_interactive(files):
    """Displays files and asks user to select one."""
    print("\n📂 Found JSON files:")
    for i, filename in enumerate(files, 1):
        mtime = os.path.getmtime(filename)
        size = os.path.getsize(filename)
        print(f"  [{i}] {filename:<40} ({format_timestamp(mtime)}) - {size} bytes")
    
    print(f"  [q] Quit")
    
    while True:
        choice = input("\n👉 Select a file number to push (or 'q' to quit): ").strip().lower()
        
        if choice == 'q':
            print("Bye!")
            sys.exit(0)
            
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return files[idx]
            else:
                print("❌ Invalid number. Please try again.")
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'q'.")

def push_to_webhook(filename):
    if not N8N_WEBHOOK_URL:
        print("❌ Error: N8N_WEBHOOK_URL is not configured in config.py")
        sys.exit(1)

    print(f"\n📄 Reading file: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"🚀 Sending data to: {N8N_WEBHOOK_URL}")
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(N8N_WEBHOOK_URL, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Success! Data sent to webhook.")
        else:
            print(f"⚠️ Failed. Webhook returned status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found.")
    except json.JSONDecodeError:
        print(f"❌ Error: File '{filename}' is not valid JSON.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def main():
    print("="*60)
    print("   MANUAL WEBHOOK PUSH INTERFACE")
    print("="*60)

    target_file = None
    
    # 1. Check command line arguments
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        print(f"👉 Using file from argument: {target_file}")
    else:
        # 2. Interactive selection
        files = get_json_files()
        if not files:
            print("❌ No JSON files found in current directory.")
            sys.exit(1)
            
        target_file = select_file_interactive(files)
            
    # 3. Push
    if target_file:
        push_to_webhook(target_file)

if __name__ == "__main__":
    main()
