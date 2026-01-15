import requests
import time
import warnings
import sys
import os
import json
from collections import Counter
from datetime import datetime

# Disable insecure request warnings for local API
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
try:
    from config import N8N_WEBHOOK_URL
except ImportError:
    print("⚠️ config.py not found. Please create it with N8N_WEBHOOK_URL.")
    N8N_WEBHOOK_URL = None
# ---------------------

class GameMonitor:
    def __init__(self, poll_interval=1.0):
        self.url = "https://127.0.0.1:2999/liveclientdata/allgamedata"
        self.poll_interval = poll_interval
        self.reset_state()

    def reset_state(self):
        # State tracking
        self.previous_items = []
        self.previous_level = 0
        self.previous_kda = (0, 0, 0)
        self.previous_game_time = 0
        
        self.is_first_run = True
        self.active_player_name = None
        self.champion_name = None
        self.game_result = None  # "Win", "Lose", or None
        
        # History for Export
        self.event_log = []
        self.final_stats = {}

        # Death Tracking
        self.death_tracking_target = None
        self.death_tracking_count = 0

    def fetch_data(self):
        try:
            # Short timeout to detect game end quickly
            response = requests.get(self.url, verify=False, timeout=1.0)
            if response.status_code == 200:
                return response.json()
            return None
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
            return None
        except Exception:
            return None

    def format_time(self):
        mins = int(self.previous_game_time // 60)
        secs = int(self.previous_game_time % 60)
        return f"{mins:02d}:{secs:02d}"

    def log_event(self, event_type, details):
        timestamp = self.format_time()
        # Clear the current status line before printing the event
        sys.stdout.write("\r" + " " * 100 + "\r")
        print(f"[{timestamp}] {event_type}: {details}")
        
        self.event_log.append({
            "game_time": self.previous_game_time,
            "formatted_time": timestamp,
            "type": event_type,
            "details": details
        })

    def process_items(self, current_item_objects):
        current_item_names = [item['displayName'] for item in current_item_objects]
        
        if self.is_first_run:
            self.previous_items = current_item_names
            return

        curr_counts = Counter(current_item_names)
        prev_counts = Counter(self.previous_items)
        
        new_items = []
        for item, count in curr_counts.items():
            prev_count = prev_counts.get(item, 0)
            if count > prev_count:
                new_items.extend([item] * (count - prev_count))
                
        if new_items:
            for item in new_items:
                self.log_event("💰 ITEM BOUGHT", item)

        # Check for Sold Items
        sold_items = []
        for item, prev_count in prev_counts.items():
            curr_count = curr_counts.get(item, 0)
            if prev_count > curr_count:
                sold_items.extend([item] * (prev_count - curr_count))
                
        if sold_items:
            for item in sold_items:
                self.log_event("💸 ITEM SOLD", item)
        
        self.previous_items = current_item_names

    def export_data(self):
        if not self.active_player_name:
            return # Minimal data, skip export

        print(f"\nExample Exporting data to n8n...")
        
        payload = {
            "type": "MatchSummary",
            "timestamp": datetime.now().isoformat(),
            "player": self.active_player_name,
            "champion": self.champion_name,
            "result": self.game_result,
            "stats": self.final_stats,
            "timeline": self.event_log
        }
        
        # --- SAVE TO FILE ---
        try:
            # Construct a professional filename
            # Formatters: Date_Time_Champion_Result.json
            now_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
            champ_str = self.champion_name if self.champion_name else "UnknownChamp"
            result_str = self.game_result if self.game_result else "Played"
            
            filename = f"{now_str}_{champ_str}_{result_str}.json"
            
            # Sanitize filename just in case
            filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.')).strip()
            
            # Ensure folder exists
            output_dir = "matches"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            print(f"💾 Saved match data to '{filepath}'")
        except Exception as e:
            print(f"❌ Error saving to file: {e}")

        # --- N8N EXPORT ---
        if N8N_WEBHOOK_URL and "YOUR_N8N_WEBHOOK_URL" not in N8N_WEBHOOK_URL:
            try:
                # Use a proper timeout so we don't hang if n8n is slow
                resp = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
                if resp.status_code == 200:
                    print("✅ Data successfully sent to n8n!")
                else:
                    print(f"⚠️ Failed to send to n8n. Status: {resp.status_code}")
            except Exception as e:
                print(f"❌ Error sending to n8n: {e}")
        else:
            print("ℹ️ n8n URL not configured.")
            print(f"   (Data is saved in '{filepath}')")
        # ------------------

    def trigger_death_webhook(self, name, deaths):
        """Triggers webhook specifically for player death."""
        if not N8N_WEBHOOK_URL:
            return
            
        # Payload specifically tailored for the death alert
        payload = {
            "type": "DeathAlert", 
            "summonerName": name,
            "deathCount": deaths
        }
        
        try:
            # Fire and forget (short timeout)
            resp = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=2)
            if resp.status_code != 200:
                print(f"⚠️ Death Webhook Failed: {resp.status_code}")
            else:
                 print(f"📡 Death Webhook Sent ({resp.status_code})")
        except Exception as e:
            print(f"⚠️ Death Webhook Error: {e}")

    def setup_death_tracking(self, data):
        """Interactively ask user to track a teammate's deaths."""
        try:
            active_name = data.get('activePlayer', {}).get('summonerName')
            all_players = data.get('allPlayers', [])
            
            if not active_name or not all_players:
                return # Can't setup yet

            # Identifiy team
            my_team = None
            for p in all_players:
                if p['summonerName'] == active_name:
                    my_team = p.get('team')
                    break
            
            if not my_team:
                return

            print("\n" + "-"*30)
            print("   DEATH TRACKER SETUP")
            print("-"*30)
            
            # Flush to ensure visibility
            sys.stdout.flush()
            
            print("Would you like to track a teammate's deaths? (y/n)")
            choice = input("> ").strip().lower()
            if choice != 'y':
                print("Skipping death tracking.")
                return

            # List teammates
            team_members = [p for p in all_players if p.get('team') == my_team]
            
            print("\nSelect player to track:")
            for i, p in enumerate(team_members):
                print(f"{i+1}. {p['summonerName']} ({p['championName']})")
                
            sel = input("Enter number > ").strip()
            if not sel.isdigit():
                print("Invalid input. Skipping.")
                return
                
            idx = int(sel) - 1
            if 0 <= idx < len(team_members):
                target_p = team_members[idx]
                self.death_tracking_target = target_p['summonerName']
                self.death_tracking_count = target_p['scores']['deaths']
                print(f"✅ Tracking: {self.death_tracking_target} (Starting Deaths: {self.death_tracking_count})")
            else:
                print("Invalid number. Skipping.")
                
        except Exception as e:
            print(f"Error during setup: {e}") 


    def monitor_game(self):
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Game Connected! Initializing monitor...")
        self.reset_state()
        
        # Wait for data to be ready for setup
        print("Waiting for player data to be ready...")
        setup_data = None
        for _ in range(10): 
            setup_data = self.fetch_data()
            if setup_data and setup_data.get('allPlayers') and setup_data.get('activePlayer', {}).get('summonerName'):
                break
            time.sleep(1)
            
        if setup_data:
            self.setup_death_tracking(setup_data)
        else:
            print("Timed out waiting for player data. Skipping death tracker setup.")

        
        fail_count = 0
        max_fails = 5 # Grace period for alt-tabs or lag

        while True:
            data = self.fetch_data()
            
            if not data:
                fail_count += 1
                if fail_count >= max_fails:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Game Disconnected.")
                    self.export_data() # <--- TRIGGER EXPORT ON END
                    return 
                time.sleep(self.poll_interval)
                continue
            
            fail_count = 0 

            try:
                game_time = data['gameData']['gameTime']
                self.previous_game_time = game_time
                
                # Identify Player
                if not self.active_player_name:
                    self.active_player_name = data['activePlayer']['summonerName']
                    # Need to find champion name from allPlayers to be accurate
                    p_data = next((p for p in data['allPlayers'] if p['summonerName'] == self.active_player_name), None)
                    if p_data:
                        self.champion_name = p_data['championName']
                    print(f"Tracking Player: {self.active_player_name} ({self.champion_name})")

                player_data = next((p for p in data['allPlayers'] if p['summonerName'] == self.active_player_name), None)
                
                if not player_data:
                    time.sleep(self.poll_interval)
                    continue

                scores = player_data['scores']
                items = player_data['items']
                level = player_data['level']
                creep_score = scores['creepScore']

                # Update Final Stats each tick so we have the latest when it crashes
                self.final_stats = {
                    "kills": scores['kills'],
                    "deaths": scores['deaths'],
                    "assists": scores['assists'],
                    "cs": creep_score,
                    "level": level,
                    "gold": data['activePlayer']['currentGold']
                }

                # --- Events ---
                
                # Check Global Events for Game End / Result
                if 'events' in data and 'Events' in data['events']:
                    for evt in data['events']['Events']:
                        if evt.get('EventName') == "GameEnd":
                            self.game_result = evt.get('Result', 'Finished') # "Win" or "Lose" usually

                # 1. Level Up
                if level > self.previous_level:
                    if not self.is_first_run:
                        self.log_event("🆙 LEVEL UP", str(level))
                    self.previous_level = level

                # 2. Items
                self.process_items(items)

                # 3. KDA
                k, d, a = scores['kills'], scores['deaths'], scores['assists']
                if (k, d, a) != self.previous_kda:
                    if not self.is_first_run:
                        self.log_event("⚔️ KDA UPDATE", f"{k}/{d}/{a}")
                    self.previous_kda = (k, d, a)

                # 4. Custom Death Tracking
                if self.death_tracking_target:
                    # Find the specific player
                    target_p = next((p for p in data['allPlayers'] if p['summonerName'] == self.death_tracking_target), None)
                    if target_p:
                        curr_deaths = target_p['scores']['deaths']
                        if curr_deaths > self.death_tracking_count:
                            self.log_event("💀 TEAMMATE DIED", f"{self.death_tracking_target} ({curr_deaths} deaths)")
                            self.trigger_death_webhook(self.death_tracking_target, curr_deaths)
                            self.death_tracking_count = curr_deaths

                self.is_first_run = False

                # --- Live Status Bar ---
                # [12:30] Vi (Lvl 9) | KDA: 3/1/2 | CS: 80 | Gold: 1200
                status_line = f"[{self.format_time()}] {self.active_player_name} (Lvl {level}) | KDA: {k}/{d}/{a} | CS: {creep_score} | 💰 {int(data['activePlayer']['currentGold'])}"
                sys.stdout.write(f"\r{status_line}")
                sys.stdout.flush()
                
            except KeyError:
                pass
            
            time.sleep(self.poll_interval)

def main():
    monitor = GameMonitor()
    print("="*50)
    print("   LEAGUE MATCH RECORDER (Auto-Pilot)")
    print(f"   Webhook: {N8N_WEBHOOK_URL}")
    print("   Waiting for match to start...")
    print("="*50)

    try:
        while True:
            data = monitor.fetch_data()
            if data:
                monitor.monitor_game()
                print("Waiting for next match... (Press Ctrl+C to quit)")
            else:
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\nExiting. GG!")
        sys.exit(0)

if __name__ == "__main__":
    main()
