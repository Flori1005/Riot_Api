import requests
import sys

# Import configuration
try:
    from config import N8N_WEBHOOK_URL
except ImportError:
    print("❌ Error: config.py not found.")
    print("   Please create 'config.py' with: N8N_WEBHOOK_URL = '...'")
    sys.exit(1)

def send_death_alert(name, deaths):
    if not N8N_WEBHOOK_URL:
        print("❌ Error: N8N_WEBHOOK_URL is not configured.")
        return

    payload = {
        "type": "DeathAlert", 
        "summonerName": name,
        "deathCount": int(deaths)
    }
    
    print(f"🚀 Sending DeathAlert for {name} ({deaths} deaths)...")
    
    try:
        headers = {'Content-Type': 'application/json'}
        resp = requests.post(N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            print("✅ Webhook Sent Successfully!")
        else:
            print(f"⚠️ Failed. Status: {resp.status_code}")
            print(f"   Response: {resp.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("="*60)
    print("   MANUAL DEATH ALERT TRIGGER")
    print("="*60)
    
    while True:
        print("\nEnter details (or 'q' to quit):")
        
        name = input("👤 Summoner Name: ").strip()
        if name.lower() == 'q':
            break
            
        deaths = input("💀 Death Count: ").strip()
        if deaths.lower() == 'q':
            break
            
        if not deaths.isdigit():
            print("❌ Invalid death count. Please enter a number.")
            continue
            
        send_death_alert(name, deaths)
        
    print("Bye!")

if __name__ == "__main__":
    main()
