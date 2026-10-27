# 🗳️ Salumber Panchayati Raj Election Live Results Portal 2026
## Standalone Real-Time Election Broadcast System & Embedded Database

Official high-performance live election counting and display system for **Salumber District (Rajasthan) Panchayati Raj Elections 2026** (21 Zilla Parishad Wards & 105 Panchayat Samiti Wards across 7 Blocks).

* **GitHub Repository**: [https://github.com/narendragd999/CountingDisplay.git](https://github.com/narendragd999/CountingDisplay.git)
* **Local Offline Engine**: Python FastAPI + SQLite + WebSockets (<5ms live push)
* **Global Public Broadcast**: Cloudflare Tunnel (`cloudflared`) with zero configuration

---

## 🚀 How to Run

### Option A: Local Hall & LAN Broadcast (Offline Safe)
Double-click:
👉 **`start.bat`**
* **📺 TV Big Screen Display (1080p / 4K)**: [http://localhost:8000/](http://localhost:8000/)
* **📝 Operator Vote Entry Console**: [http://localhost:8000/entry](http://localhost:8000/entry)
* **📥 1-Click Results CSV Export**: [http://localhost:8000/api/export_csv](http://localhost:8000/api/export_csv)

### Option B: Cloudflare Live Public Broadcast (Internet / Mobile Viewers)
Double-click:
👉 **`start_with_cloudflare.bat`**
* Automatically starts the local server and connects to the **Cloudflare Global Edge Network** using `cloudflared`.
* Prints a public HTTPS URL (e.g. `https://xxxx.trycloudflare.com`) in the terminal.
* Share that link with District Collectors, Returning Officers, Media, and Mobile Viewers anywhere in the world with full live WebSocket updates!

---

## ☁️ Cloudflare Hosting Guide

### Method 1: Cloudflare Tunnel (Recommended)
1. Run `start_with_cloudflare.bat`.
2. Cloudflare automatically establishes an encrypted tunnel between your local counting machine and Cloudflare's global edge.
3. Features:
   * **100% Offline Resilience**: If the internet drops, local counting on `localhost:8000` continues without interruption.
   * **Full WebSockets**: Sub-millisecond push updates to all online viewers.
   * **DDoS Protected**: Backed by Cloudflare enterprise network security.

### Method 2: Cloudflare Pages (Static Frontend from GitHub)
1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/) → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**.
2. Select repository: `narendragd999/CountingDisplay`.
3. Set **Build output directory** to: `public`.
4. Click **Save and Deploy**.

---

## 🌟 Key Election Features & Safety Controls

1. **Devanagari Hindi Alphabetical Ordering (वर्णमाला क्रमानुसार)**:
   * All 275 candidates are strictly sorted in Hindi alphabetical order according to Rajasthan State Election Commission Form 7A rules.
   * Candidates display their official EVM Ballot Serial Number (`क्र.सं. 1`, `क्र.सं. 2`...).
2. **Interactive TV Ward Filters & Pause / Play**:
   * Direct dropdown filter on the big screen TV to jump to any of the 21 ZP wards or 105 PS wards instantly.
   * `⏸ Pause` / `▶ Play` button to freeze the auto-rotation on any ward during inspection.
3. **Round-Wise Entry vs. Automatic Cumulative Summation**:
   * Operators enter only the votes counted in that specific round (`Round Votes`).
   * The system automatically accumulates previous rounds into the **Cumulative Total (कुल संचयी योग)** with a real-time live preview.
4. **Faulty EVM Protocol (Without VVPAT)**:
   * Counting at other tables never stops.
   * When a faulty machine is resolved via Auxiliary Display Unit (ADU) or power replacement, enter votes under the round or select `Faulty EVM Resolved / Aux Display`.
5. **No Premature Declaration**:
   * Wards with 0 entered votes can never be marked as `DECLARED`.
   * Unearned leads are never awarded on zero votes.
6. **Recount / Mistake Correction Unlocking**:
   * Any declared ward can be re-opened for recount or corrections via the `🔓 UNLOCK / REOPEN WARD FOR EDITING` button.
7. **Pre-Counting Hall Setup**:
   * Built-in `⚙️ Hall & Rounds Setup` tool allows Returning Officers to configure counting tables (e.g., 5 or 6 tables) and booths per ward before counting day.

---

## 📂 Project Structure

```
CountingDisplay/
│
├── start.bat                   # 1-Click Local LAN / Hall Launcher
├── start_with_cloudflare.bat   # 1-Click Cloudflare Public Live Broadcast
├── app.py                      # FastAPI + SQLite + WebSocket Engine
├── election_salumber_2026.db   # Seeded SQLite Database (Clean 0-Vote State)
├── requirements.txt            # Python Dependencies (fastapi, uvicorn)
│
├── public/
│   ├── index.html              # 50/50 TV Broadcast Screen (1080p/4K)
│   └── entry.html              # Mobile/Desktop Operator Vote Entry Console
│
├── 0_Candidate_Master.csv      # Form 7A Alphabetical Candidate Directory
├── 0_Master_Setup.csv          # District & Ward Metadata
├── 1_ZP_Entry.csv              # Zilla Parishad Counting Master
├── 2_PS_Entry.csv              # Panchayat Samiti Counting Master
└── 3_ZP_Booths.csv             # 522 Polling Booths & Tables Mapping
```
