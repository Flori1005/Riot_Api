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

def find_latest_match_file():
    """Finds the most recently modified match JSON file in the current directory."""
    # Look for files matching the pattern *_*_*.json or latest_match.json
    # We'll use a generic .json search but try to filter out obviously wrong ones if needed
    json_files = glob.glob("*.json")
    
    if not json_files:
        return None
        
    # Exclude files that are definitely not match data if possible (e.g. package.json if it existed)
    # For now, just sort by modification time
    
    latest_file = max(json_files, key=os.path.getmtime)
    return latest_file

def push_to_webhook(filename):
    if not N8N_WEBHOOK_URL:
        print("❌ Error: N8N_WEBHOOK_URL is not configured in config.py")
        sys.exit(1)

    print(f"📄 Reading file: {filename}")
    
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
    print("="*40)
    print("   MANUAL WEBHOOK PUSH")
    print("="*40)

    target_file = None
    
    # 1. Check command line arguments
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        # 2. Find latest file if no argument provided
        print("🔍 No file specified. Looking for latest match file...")
        latest = find_latest_match_file()
        if latest:
            print(f"👉 Found latest file: {latest}")
            target_file = latest
        else:
            print("❌ No JSON files found in current directory.")
            sys.exit(1)
            
    # 3. Confirmation (optional, but good for manual tools)
    # We'll skip explicit confirmation for speed as requested "whenever I want"
    
    push_to_webhook(target_file)

if __name__ == "__main__":
    main()
