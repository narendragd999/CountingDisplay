# Salumber Panchayati Raj Election Live Results Portal 2026
## Standalone Real-Time Election Broadcast System & Embedded Database

This is the standalone, high-performance Live Election Results Portal and Operator Console for **Salumber District (Rajasthan) Panchayati Raj Elections 2026**.

It eliminates all dependencies on Google Sheets and cloud services. It runs locally with an embedded SQLite database and WebSockets, providing sub-millisecond real-time live broadcast to big screen TVs (1080p / 4K).

---

## 🚀 1-Click Launch (Windows)

Simply double-click:
👉 **`start.bat`**

This starts the server and automatically opens both interfaces in your browser:
* **📺 TV Broadcast Screen**: [http://localhost:8000/](http://localhost:8000/) *(Press `F11` for full screen)*
* **📝 Operator Vote Entry Console**: [http://localhost:8000/entry](http://localhost:8000/entry)
* **📥 Instant CSV Export**: [http://localhost:8000/api/export_csv](http://localhost:8000/api/export_csv)

---

## 📱 Multi-Operator Network Setup (Counting Hall Wi-Fi / LAN)

Multiple operators on different laptops, tablets, or phones can enter votes simultaneously without conflicting:

1. Connect the counting hall computers/phones to the same Wi-Fi or LAN.
2. Find the server computer's IP address (e.g. `192.168.1.15`).
3. Operators open:
   `http://192.168.1.15:8000/entry`
4. The big screen TV opens:
   `http://192.168.1.15:8000/`

Whenever any operator clicks **"SAVE ROUND VOTES"**, the TV display updates across the hall in **under 5 milliseconds via WebSockets**.

---

## 📂 Project Structure

```
CountingDisplay/
│
├── start.bat                   # 1-Click Windows desktop launcher
├── app.py                      # FastAPI + SQLite + WebSocket server
├── election_salumber_2026.db   # Embedded SQLite database (pre-seeded)
│
├── public/
│   ├── index.html              # Pure 50/50 TV Broadcast Screen (1080p/4K)
│   └── entry.html              # Mobile/Desktop Operator Vote Entry Console
│
├── 0_Candidate_Master.csv      # CSV export of all 275 official candidates
├── 0_Master_Setup.csv          # CSV export of all 21 ZP & 105 PS wards
├── 1_ZP_Entry.csv              # CSV format for ZP live entries
├── 2_PS_Entry.csv              # CSV format for PS live entries
└── 3_ZP_Booths.csv             # CSV export of all 522 polling booths
```

---

## 🏛️ Election Data Coverage

* **Zilla Parishad (ZP) Salumber**: All 21 Wards (79 official candidates, 522 booths, 5 tables per ward).
* **Panchayat Samitis (7 Blocks)**: 
  * *Semari* (15 Wards, 54 candidates)
  * *Salumbar* (15 Wards, 49 candidates)
  * *Lasadiya* (15 Wards, 50 candidates)
  * *Geengla* (15 Wards, 43 candidates)
  * *Jaisamand, Sarada, Jhallara* (Templates ready; add candidates via the console anytime)
