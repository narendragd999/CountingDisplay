import app
import json
import datetime
import os
import shutil

# 1. First, make sure we have a timestamped backup of the local sqlite db in backups/
os.makedirs("backups", exist_ok=True)
now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
db_backup = f"backups/election_salumber_backup_LOCAL_SAFE_{now_str}.db"
if os.path.exists("election_salumber_2026.db"):
    shutil.copy2("election_salumber_2026.db", db_backup)
    print(f"Safety SQLite Backup: {db_backup} ({os.path.getsize(db_backup)} bytes)")

# 2. Export full snapshot data
master = app.get_all_candidates_master()

timestamp_fname = f"election_salumber_snapshot_{now_str}.json"
with open(timestamp_fname, "w", encoding="utf-8") as f:
    json.dump(master, f, ensure_ascii=False, indent=2)

with open("election_salumber_latest_snapshot.json", "w", encoding="utf-8") as f:
    json.dump(master, f, ensure_ascii=False, indent=2)

print(f"JSON Snapshot: {timestamp_fname} ({os.path.getsize(timestamp_fname)} bytes)")
print(f"Latest Snapshot: election_salumber_latest_snapshot.json ({os.path.getsize('election_salumber_latest_snapshot.json')} bytes)")
print(f"Votes Count: {len(master.get('roundVotes', {}))} candidates with entered votes")
