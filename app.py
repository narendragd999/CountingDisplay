# app.py
"""
SALUMBER DISTRICT PANCHAYATI RAJ ELECTIONS 2026
Standalone High-Performance Election Server & Database
FastAPI + SQLite + WebSockets + 0ms Real-Time Push
"""

import os
import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

DB_FILE = "election_salumber_2026.db"

PS_BLOCKS = [
    'Semari', 'Salumbar', 'Lasadiya', 'Geengla', 'Jaisamand', 'Sarada', 'Jhallara'
]

PARTY_COLORS = {
    'BJP': '#ea580c',
    'INC': '#0284c7',
    'BAP': '#ca8a04',
    'AAP': '#0d9488',
    'IND': '#64748b'
}

# Active WebSocket connections for instant live TV updates
active_connections: List[WebSocket] = []

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initializes SQLite schema and seeds official data if fresh."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Wards Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,          -- 'ZP' or 'PS'
        block_name TEXT NOT NULL,        -- 'Salumber ZP', 'Semari', etc.
        ward_no INTEGER NOT NULL,
        ward_name_hindi TEXT,
        reservation TEXT DEFAULT 'ST',
        total_booths INTEGER DEFAULT 25,
        counting_tables INTEGER DEFAULT 5,
        max_rounds INTEGER DEFAULT 5,
        total_electorate INTEGER DEFAULT 20000,
        status TEXT DEFAULT 'COUNTING',   -- 'COUNTING' or 'DECLARED'
        UNIQUE(category, block_name, ward_no)
    )
    """)

    # 2. Candidates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,          -- 'ZP' or 'PS'
        block_name TEXT NOT NULL,
        ward_no INTEGER NOT NULL,
        name_hindi TEXT NOT NULL,
        party TEXT NOT NULL,
        symbol TEXT DEFAULT 'Official',
        gender TEXT,
        age TEXT,
        candidate_category TEXT,
        ballot_no INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1
    )
    """)

    # 3. Votes Table (Round by Round)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        round_key TEXT NOT NULL,          -- 'PB', 'R1', 'R2', etc.
        votes_count INTEGER NOT NULL DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(candidate_id, round_key),
        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
    )
    """)

    # 4. Booths Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS booths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booth_no TEXT NOT NULL,
        ward_no INTEGER NOT NULL,
        ps_block TEXT,
        station_name TEXT,
        total_electors INTEGER DEFAULT 0,
        table_no TEXT,
        round_no TEXT
    )
    """)

    # 5. Audit Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        action TEXT,
        details TEXT
    )
    """)

    conn.commit()

    # Seed Wards if empty
    cursor.execute("SELECT COUNT(*) FROM wards")
    if cursor.fetchone()[0] == 0:
        seed_initial_data(conn)

    conn.close()

def seed_initial_data(conn):
    """Seeds official ZP wards, PS blocks, 275 candidates, and 522 booths."""
    cursor = conn.cursor()
    print("Seeding initial database with official Salumber election data...")

    # Load booths & ward stats
    if os.path.exists('zp_booths_processed.json'):
        with open('zp_booths_processed.json', 'r', encoding='utf-8') as f:
            b_data = json.load(f)
            ward_stats = b_data.get('wardStats', {})
            all_booths = b_data.get('allBooths', [])

            # Insert 21 ZP Wards
            for w in range(1, 22):
                st = ward_stats.get(str(w), {})
                cursor.execute("""
                INSERT OR IGNORE INTO wards 
                (category, block_name, ward_no, ward_name_hindi, reservation, total_booths, counting_tables, max_rounds, total_electorate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'ZP', 'Salumber ZP', w, st.get('wardNameHindi', f'वार्ड {w}'),
                    st.get('reservation', 'ST'), st.get('totalBooths', 25), 5,
                    st.get('maxRounds', 5), st.get('totalElectorate', 22000)
                ))

            # Insert Booths
            for b in all_booths:
                w = b['wardNo']
                idx = b.get('srn', 1)
                cursor.execute("""
                INSERT INTO booths (booth_no, ward_no, ps_block, station_name, total_electors, table_no, round_no)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    b.get('boothNo', ''), w, get_block_for_zp_ward(w),
                    b.get('boothName', ''), b.get('totalElectorate', 0),
                    f"Table {((int(idx)-1) % 5) + 1}", f"Round {((int(idx)-1) // 5) + 1}"
                ))

    # Insert 7 PS Blocks x 15 Wards
    for b in PS_BLOCKS:
        for w in range(1, 16):
            cursor.execute("""
            INSERT OR IGNORE INTO wards 
            (category, block_name, ward_no, ward_name_hindi, reservation, total_booths, counting_tables, max_rounds, total_electorate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'PS', b, w, f'{b} वार्ड {w}', 'ST', 5, 5, 2, 4500
            ))

    # Load All Candidates
    if os.path.exists('all_candidates_master.json'):
        with open('all_candidates_master.json', 'r', encoding='utf-8') as f:
            all_cands = json.load(f)
            for c in all_cands:
                cursor.execute("""
                INSERT INTO candidates (category, block_name, ward_no, name_hindi, party, symbol, gender, age, candidate_category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c['type'], c['block'], c['wardNo'], c['name'], c['party'],
                    c.get('symbol', 'Official'), c.get('gender', ''), str(c.get('age', '')), c.get('category', '')
                ))

    conn.commit()
    print("Database seeding completed successfully!")

def get_block_for_zp_ward(w: int) -> str:
    if 1 <= w <= 3: return 'Jaisamand'
    if 4 <= w <= 6: return 'Sarada'
    if 7 <= w <= 9: return 'Semari'
    if 10 <= w <= 12: return 'Salumbar'
    if 13 <= w <= 15: return 'Geengla'
    if 16 <= w <= 18: return 'Lasadiya'
    return 'Jhallara'

def normalize_party(p: str) -> str:
    u = str(p or '').strip().upper()
    if 'BAP' in u or 'आदिवासी' in u: return 'BAP'
    if 'BJP' in u or 'भाजपा' in u: return 'BJP'
    if 'INC' in u or 'कांग्रेस' in u: return 'INC'
    if 'AAP' in u or 'आम आदमी' in u: return 'AAP'
    return 'IND'

def calculate_full_state():
    """Builds complete election JSON payload identical to what index.html needs."""
    conn = get_db()
    cursor = conn.cursor()

    # Fetch all wards
    cursor.execute("SELECT * FROM wards ORDER BY category, block_name, ward_no")
    wards_rows = cursor.fetchall()

    # Fetch all candidates with their votes
    cursor.execute("""
    SELECT c.*, 
           COALESCE(SUM(v.votes_count), 0) as total_votes,
           COALESCE((SELECT votes_count FROM votes WHERE candidate_id = c.id AND round_key = 'PB'), 0) as pb_votes
    FROM candidates c
    LEFT JOIN votes v ON c.id = v.candidate_id
    WHERE c.is_active = 1
    GROUP BY c.id
    ORDER BY c.category, c.block_name, c.ward_no, total_votes DESC, c.ballot_no ASC, c.name_hindi ASC
    """)
    candidates_rows = cursor.fetchall()

    # Fetch round votes per candidate
    cursor.execute("SELECT candidate_id, round_key, votes_count FROM votes")
    round_votes_map = {}
    for r in cursor.fetchall():
        cid = r['candidate_id']
        if cid not in round_votes_map: round_votes_map[cid] = {}
        round_votes_map[cid][r['round_key']] = r['votes_count']

    conn.close()

    # Group candidates by (category, block_name, ward_no)
    cands_by_ward = {}
    for c in candidates_rows:
        key = (c['category'], c['block_name'], c['ward_no'])
        if key not in cands_by_ward: cands_by_ward[key] = []
        c_dict = dict(c)
        c_dict['roundVotes'] = round_votes_map.get(c['id'], {})
        cands_by_ward[key].append(c_dict)

    zp_wards = []
    ps_wards = []
    zp_declared_count = 0
    ps_declared_count = 0

    zp_tally = {p: {'won': 0, 'lead': 0, 'total': 0} for p in ['BJP', 'INC', 'BAP', 'AAP', 'IND']}
    ps_tally = {p: {'won': 0, 'lead': 0, 'total': 0} for p in ['BJP', 'INC', 'BAP', 'AAP', 'IND']}

    ticker_items = []

    for w in wards_rows:
        w_dict = dict(w)
        key = (w['category'], w['block_name'], w['ward_no'])
        cands = cands_by_ward.get(key, [])

        # Sort candidates: by total_votes DESC; on tie or 0 votes, by ballot_no ASC (Hindi alphabetical)
        cands.sort(key=lambda x: (x['total_votes'], -(x.get('ballot_no') or 99)), reverse=True)

        c1 = cands[0] if len(cands) > 0 else {'name_hindi': 'प्रत्याशी 1', 'party': 'BAP', 'total_votes': 0, 'pb_votes': 0, 'roundVotes': {}}
        c2 = cands[1] if len(cands) > 1 else {'name_hindi': 'प्रत्याशी 2', 'party': 'BJP', 'total_votes': 0, 'pb_votes': 0, 'roundVotes': {}}

        c1_tot = c1['total_votes']
        c2_tot = c2['total_votes']
        has_votes = (c1_tot > 0 or c2_tot > 0)
        margin = max(0, c1_tot - c2_tot)

        # Detect completed rounds
        completed_rounds = 0
        c1_rounds = c1.get('roundVotes', {})
        for r in range(1, w['max_rounds'] + 1):
            if f'R{r}' in c1_rounds:
                completed_rounds = r

        is_declared = (w['status'] == 'DECLARED' and has_votes)
        if is_declared:
            completed_rounds = w['max_rounds']
        elif not has_votes:
            completed_rounds = 0

        round_progress_pct = int((completed_rounds / w['max_rounds']) * 100) if (w['max_rounds'] > 0 and has_votes) else 0

        # Build round progression table
        round_table = []
        c2_rounds = c2.get('roundVotes', {})
        for r in range(1, w['max_rounds'] + 1):
            r_key = f'R{r}'
            v1 = c1_rounds.get(r_key)
            v2 = c2_rounds.get(r_key)
            is_done = (v1 is not None)
            round_table.append({
                'round': r_key,
                'roundNo': r,
                'winnerVotes': v1,
                'runnerVotes': v2,
                'diff': (v1 - v2) if (is_done and v2 is not None) else None,
                'isCompleted': is_done
            })

        c1_party = normalize_party(c1['party'])
        c2_party = normalize_party(c2['party'])

        ward_obj = {
            'id': w['id'],
            'category': w['category'],
            'blockName': w['block_name'],
            'wardNo': w['ward_no'],
            'wardNameHindi': w['ward_name_hindi'] or f"वार्ड {w['ward_no']}",
            'reservation': w['reservation'],
            'totalBooths': w['total_booths'],
            'countingTables': w['counting_tables'],
            'maxRounds': w['max_rounds'],
            'currentRound': completed_rounds,
            'roundProgressPct': round_progress_pct,
            'status': 'DECLARED' if is_declared else 'COUNTING',
            'winner': {
                'id': c1.get('id'),
                'name': c1['name_hindi'],
                'party': c1_party,
                'totalVotes': c1_tot,
                'pbVotes': c1['pb_votes'],
                'roundVotes': c1_rounds
            },
            'runnerUp': {
                'id': c2.get('id'),
                'name': c2['name_hindi'],
                'party': c2_party,
                'totalVotes': c2_tot,
                'pbVotes': c2['pb_votes'],
                'roundVotes': c2_rounds
            },
            'margin': margin,
            'hasVotes': has_votes,
            'roundTable': round_table,
            'candidates': [{'id': x.get('id'), 'name': x['name_hindi'], 'party': normalize_party(x['party']), 'totalVotes': x['total_votes'], 'ballotNo': x.get('ballot_no', 1)} for x in sorted(cands, key=lambda k: (k.get('ballot_no') or 99))]
        }

        # Update tallies & ticker strictly when votes exist
        target_tally = zp_tally if w['category'] == 'ZP' else ps_tally
        if has_votes:
            if is_declared:
                target_tally[c1_party]['won'] += 1
                target_tally[c1_party]['total'] += 1
            elif margin > 0:
                target_tally[c1_party]['lead'] += 1
                target_tally[c1_party]['total'] += 1

        if is_declared:
            if w['category'] == 'ZP': zp_declared_count += 1
            else: ps_declared_count += 1
            ticker_items.append(f"🏆 {w['block_name']} वार्ड {w['ward_no']} विजयी: {c1['name_hindi']} ({c1_party}) घोषित! (+{margin:,} मत)")
        elif has_votes and margin > 150:
            ticker_items.append(f"⚡ {w['block_name']} वार्ड {w['ward_no']}: {c1['name_hindi']} ({c1_party}) बढ़त +{margin:,} मत (राउंड {completed_rounds}/{w['max_rounds']})")

        if w['category'] == 'ZP':
            zp_wards.append(ward_obj)
        else:
            ps_wards.append(ward_obj)

    if not ticker_items:
        ticker_items = [
            "★ सलूंबर जिला परिषद एवं 7 पंचायत समितियों के मतगणना परिणाम लाइव",
            "प्रत्येक वार्ड में 5 काउंटिंग टेबल्स पर मतों की गिनती शांतिपूर्ण जारी है..."
        ]

    return {
        'status': 'success',
        'district': 'Salumber (सलूंबर)',
        'election': 'Panchayati Raj Elections 2026',
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'summary': {
            'zpTotalWards': 21,
            'zpDeclaredWards': zp_declared_count,
            'psTotalBlocks': len(PS_BLOCKS),
            'psTotalWards': len(ps_wards),
            'psDeclaredWards': ps_declared_count
        },
        'tallies': {
            'zp': zp_tally,
            'ps': ps_tally
        },
        'zp': {
            'wards': zp_wards,
            'declaredCount': zp_declared_count
        },
        'ps': {
            'blocks': PS_BLOCKS,
            'wards': ps_wards,
            'declaredCount': ps_declared_count
        },
        'ticker': ticker_items
    }

async def broadcast_live_update():
    """Instantly pushes the updated state to all connected TV displays via WebSockets."""
    if not active_connections:
        return
    state = calculate_full_state()
    message = json.dumps(state, ensure_ascii=False)
    for ws in active_connections[:]:
        try:
            await ws.send_text(message)
        except Exception:
            if ws in active_connections:
                active_connections.remove(ws)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield

app = FastAPI(title="Salumber Election Portal", lifespan=lifespan)

# Mount public directory for assets if needed
if os.path.exists("public"):
    app.mount("/static", StaticFiles(directory="public"), name="static")

# ==============================================================================
# WEBSOCKET FOR 0ms INSTANT TV BROADCAST
# ==============================================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send initial state immediately
        initial_state = calculate_full_state()
        await websocket.send_text(json.dumps(initial_state, ensure_ascii=False))
        while True:
            # Keep alive and listen for client pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections:
            active_connections.remove(websocket)

# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================
@app.get("/api/state")
def get_state():
    return calculate_full_state()

@app.get("/api/candidates")
def get_candidates(category: str, block: str, ward_no: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.id, c.name_hindi, c.party, c.symbol, c.ballot_no,
           COALESCE((SELECT votes_count FROM votes WHERE candidate_id = c.id AND round_key = 'PB'), '') as pb_votes
    FROM candidates c
    WHERE c.category = ? AND c.block_name = ? AND c.ward_no = ? AND c.is_active = 1
    ORDER BY c.ballot_no ASC, c.name_hindi ASC
    """, (category, block, ward_no))
    rows = cursor.fetchall()

    # Get round votes for these candidates
    c_list = []
    for r in rows:
        cid = r['id']
        cursor.execute("SELECT round_key, votes_count FROM votes WHERE candidate_id = ?", (cid,))
        r_map = {vr['round_key']: vr['votes_count'] for vr in cursor.fetchall()}
        c_list.append({
            'id': cid,
            'name': r['name_hindi'],
            'party': r['party'],
            'symbol': r['symbol'],
            'ballot_no': r['ballot_no'],
            'roundVotes': r_map
        })

    # Get ward status
    cursor.execute("SELECT status FROM wards WHERE category = ? AND block_name = ? AND ward_no = ?", (category, block, ward_no))
    w_row = cursor.fetchone()
    ward_status = w_row['status'] if w_row else 'COUNTING'

    conn.close()
    return {'candidates': c_list, 'status': ward_status}

@app.post("/api/save_votes")
async def save_votes(payload: dict):
    """
    Saves round votes atomically into SQLite and broadcasts immediately to TV!
    payload: { category, block, ward_no, round_key, votes: { cand_id: count }, declare: bool }
    """
    category = payload.get('category')
    block = payload.get('block')
    ward_no = int(payload.get('ward_no', 1))
    round_key = str(payload.get('round_key', 'R1')).upper()
    votes_dict = payload.get('votes', {})
    declare = bool(payload.get('declare', False))

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check that hall setup is confirmed for this ward
        cursor.execute("SELECT is_setup_done, max_rounds FROM wards WHERE category = ? AND block_name = ? AND ward_no = ?", (category, block, ward_no))
        w_cfg = cursor.fetchone()
        if not w_cfg or w_cfg[0] != 1:
            raise HTTPException(status_code=400, detail="Cannot enter votes: Counting Hall & Rounds setup must be confirmed for this ward before entering votes.")

        # Validate votes non-negative
        for cid_str, v_count in votes_dict.items():
            if v_count is not None and str(v_count).strip() != '':
                try:
                    val = int(v_count)
                    if val < 0:
                        raise HTTPException(status_code=400, detail="Votes cannot be negative")
                except ValueError:
                    raise HTTPException(status_code=400, detail="Votes must be valid integers")

        # Save or update each candidate's vote (or delete if cleared)
        for cid_str, v_count in votes_dict.items():
            cid = int(cid_str)
            if v_count is not None and str(v_count).strip() != '':
                val = int(v_count)
                cursor.execute("""
                INSERT INTO votes (candidate_id, round_key, votes_count)
                VALUES (?, ?, ?)
                ON CONFLICT(candidate_id, round_key) DO UPDATE SET
                    votes_count = excluded.votes_count,
                    updated_at = CURRENT_TIMESTAMP
                """, (cid, round_key, val))
            else:
                # Operator cleared the vote input - delete existing record to allow full erasure/correction
                cursor.execute("DELETE FROM votes WHERE candidate_id = ? AND round_key = ?", (cid, round_key))

        # Handle declare winner with strict data check
        if declare:
            cursor.execute("""
            SELECT COALESCE(SUM(v.votes_count), 0)
            FROM candidates c
            JOIN votes v ON c.id = v.candidate_id
            WHERE c.category = ? AND c.block_name = ? AND c.ward_no = ?
            """, (category, block, ward_no))
            total_ward_votes = cursor.fetchone()[0]
            if total_ward_votes <= 0:
                raise HTTPException(status_code=400, detail="Cannot declare ward without entered votes! At least one round of votes must be counted.")
            cursor.execute("""
            UPDATE wards SET status = 'DECLARED'
            WHERE category = ? AND block_name = ? AND ward_no = ?
            """, (category, block, ward_no))

        # Log action
        cursor.execute("""
        INSERT INTO audit_log (action, details)
        VALUES (?, ?)
        """, (
            f"SAVE_VOTES_{round_key}",
            f"{category} {block} Ward {ward_no} | Declared: {declare} | Votes: {json.dumps(votes_dict)}"
        ))

        conn.commit()
    except HTTPException:
        conn.rollback()
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    conn.close()

    # BROADCAST TO ALL CONNECTED TV SCREENS (0ms lag!)
    asyncio.create_task(broadcast_live_update())

    return {
        'status': 'success',
        'message': f"Saved {round_key} votes for {category} {block} Ward {ward_no}!",
        'declared': declare
    }

@app.post("/api/declare_ward")
async def declare_ward(payload: dict):
    category = payload.get('category')
    block = payload.get('block')
    ward_no = int(payload.get('ward_no'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(v.votes_count), 0)
    FROM candidates c
    JOIN votes v ON c.id = v.candidate_id
    WHERE c.category = ? AND c.block_name = ? AND c.ward_no = ?
    """, (category, block, ward_no))
    total_ward_votes = cursor.fetchone()[0]
    if total_ward_votes <= 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot declare ward without entered votes! At least one round of votes must be counted.")

    # Verify that all rounds are completed
    cursor.execute("SELECT max_rounds FROM wards WHERE category = ? AND block_name = ? AND ward_no = ?", (category, block, ward_no))
    max_r = cursor.fetchone()[0]
    cursor.execute("""
    SELECT COUNT(DISTINCT v.round_key)
    FROM candidates c
    JOIN votes v ON c.id = v.candidate_id
    WHERE c.category = ? AND c.block_name = ? AND c.ward_no = ? AND v.round_key LIKE 'R%'
    """, (category, block, ward_no))
    completed_r = cursor.fetchone()[0]
    if completed_r < max_r:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Cannot declare winner: All rounds must be completed! (Completed: {completed_r}/{max_r} rounds)")

    cursor.execute("""
    UPDATE wards SET status = 'DECLARED'
    WHERE category = ? AND block_name = ? AND ward_no = ?
    """, (category, block, ward_no))
    cursor.execute("""
    INSERT INTO audit_log (action, details)
    VALUES (?, ?)
    """, ("DECLARE_WARD", f"{category} {block} Ward {ward_no} declared"))
    conn.commit()
    conn.close()

    asyncio.create_task(broadcast_live_update())
    return {'status': 'success', 'message': f"{category} {block} Ward {ward_no} finalized as DECLARED!"}

@app.post("/api/reopen_ward")
async def reopen_ward(payload: dict):
    """Unlocks a declared ward back to COUNTING for recount or correction."""
    category = payload.get('category')
    block = payload.get('block')
    ward_no = int(payload.get('ward_no'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE wards SET status = 'COUNTING'
    WHERE category = ? AND block_name = ? AND ward_no = ?
    """, (category, block, ward_no))

    cursor.execute("""
    INSERT INTO audit_log (action, details)
    VALUES (?, ?)
    """, ("REOPEN_WARD", f"{category} {block} Ward {ward_no} reopened to COUNTING for recount/correction"))

    conn.commit()
    conn.close()

    asyncio.create_task(broadcast_live_update())
    return {'status': 'success', 'message': f"{category} {block} Ward {ward_no} unlocked and reopened to COUNTING!"}

@app.get("/api/all_candidates_master")
def get_all_candidates_master():
    """Returns all active candidates, wards, and existing round votes for instant 0ms operator UI switching."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.id, c.category, c.block_name, c.ward_no, c.name_hindi, c.party, c.symbol, c.ballot_no
    FROM candidates c
    WHERE c.is_active = 1
    ORDER BY c.category, c.block_name, c.ward_no, c.ballot_no ASC, c.name_hindi ASC
    """)
    c_rows = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT category, block_name, ward_no, status, max_rounds, is_setup_done, total_booths, counting_tables FROM wards")
    w_rows = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT candidate_id, round_key, votes_count FROM votes")
    votes_map = {}
    for vr in cursor.fetchall():
        cid = vr['candidate_id']
        if cid not in votes_map: votes_map[cid] = {}
        votes_map[cid][vr['round_key']] = vr['votes_count']

    conn.close()
    return {
        'candidates': c_rows,
        'wards': w_rows,
        'roundVotes': votes_map
    }

@app.post("/api/add_candidate")
async def add_candidate(payload: dict):
    """Allows adding candidates anytime for future blocks (Jaisamand, Sarada, Jhallara)."""
    category = payload.get('category')
    block = payload.get('block')
    ward_no = int(payload.get('ward_no'))
    name = payload.get('name')
    party = payload.get('party', 'IND')
    symbol = payload.get('symbol', 'Official')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO candidates (category, block_name, ward_no, name_hindi, party, symbol)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (category, block, ward_no, name, party, symbol))

    # Re-calculate ballot_no alphabetically by Hindi name for this ward
    cursor.execute("SELECT id, name_hindi FROM candidates WHERE category=? AND block_name=? AND ward_no=?", (category, block, ward_no))
    c_list = sorted(cursor.fetchall(), key=lambda x: x[1].strip())
    for b_no, (cid, cname) in enumerate(c_list, start=1):
        cursor.execute("UPDATE candidates SET ballot_no = ? WHERE id = ?", (b_no, cid))

    conn.commit()
    conn.close()

    asyncio.create_task(broadcast_live_update())
    return {'status': 'success', 'message': f"Added candidate {name} ({party}) to {category} {block} Ward {ward_no}!"}

@app.get("/api/ward_configs")
def get_ward_configs(category: Optional[str] = None, block: Optional[str] = None):
    """Returns ward configuration: booths, counting tables, max rounds, electorate, etc."""
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM wards"
    params = []
    conditions = []
    if category:
        conditions.append("category = ?")
        params.append(category)
    if block:
        conditions.append("block_name = ?")
        params.append(block)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY category, block_name, ward_no"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {'status': 'success', 'wards': rows}

@app.post("/api/save_ward_config")
async def save_ward_config(payload: dict):
    """Updates booths, counting tables, and recalculates max rounds for a specific ward."""
    import math
    category = payload.get('category')
    block = payload.get('block')
    ward_no = int(payload.get('ward_no'))
    tables = max(1, int(payload.get('counting_tables', 5)))
    booths = max(1, int(payload.get('total_booths', 25)))
    max_rounds = int(payload.get('max_rounds') or math.ceil(booths / tables))
    reservation = payload.get('reservation', 'ST')
    electorate = int(payload.get('total_electorate', 20000))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE wards SET 
        counting_tables = ?,
        total_booths = ?,
        max_rounds = ?,
        reservation = ?,
        total_electorate = ?,
        is_setup_done = 1
    WHERE category = ? AND block_name = ? AND ward_no = ?
    """, (tables, booths, max_rounds, reservation, electorate, category, block, ward_no))

    cursor.execute("""
    INSERT INTO audit_log (action, details)
    VALUES (?, ?)
    """, ("UPDATE_WARD_CONFIG", f"{category} {block} Ward {ward_no} | Tables: {tables}, Booths: {booths}, Rounds: {max_rounds}"))

    conn.commit()
    conn.close()

    asyncio.create_task(broadcast_live_update())
    return {
        'status': 'success',
        'message': f"Updated {category} {block} Ward {ward_no} config: {tables} Tables, {booths} Booths, {max_rounds} Rounds!",
        'max_rounds': max_rounds
    }

@app.post("/api/bulk_apply_hall_config")
async def bulk_apply_hall_config(payload: dict):
    """Bulk sets counting tables across an entire category or block and updates max_rounds."""
    import math
    category = payload.get('category')
    block = payload.get('block')
    tables = max(1, int(payload.get('counting_tables', 5)))

    conn = get_db()
    cursor = conn.cursor()

    if category == 'ZP':
        cursor.execute("SELECT id, total_booths FROM wards WHERE category = 'ZP'")
    elif block:
        cursor.execute("SELECT id, total_booths FROM wards WHERE category = 'PS' AND block_name = ?", (block,))
    else:
        cursor.execute("SELECT id, total_booths FROM wards WHERE category = 'PS'")

    rows = cursor.fetchall()
    for r in rows:
        wid = r['id']
        b_count = max(1, int(r['total_booths'] or 25))
        m_rounds = math.ceil(b_count / tables)
        cursor.execute("UPDATE wards SET counting_tables = ?, max_rounds = ?, is_setup_done = 1 WHERE id = ?", (tables, m_rounds, wid))

    cursor.execute("""
    INSERT INTO audit_log (action, details)
    VALUES (?, ?)
    """, ("BULK_HALL_CONFIG", f"Set {tables} tables for {category or block or 'All PS'}"))

    conn.commit()
    conn.close()

    asyncio.create_task(broadcast_live_update())
    return {'status': 'success', 'message': f"Configured {tables} counting tables for {len(rows)} wards!"}

@app.get("/api/export_csv")
def export_csv():
    """1-Click CSV export of all election results."""
    state = calculate_full_state()
    output = []
    output.append("Category,Block,Ward No,Winner Candidate,Party,Winner Total Votes,Runner-Up Candidate,Runner-Up Party,Runner-Up Total Votes,Margin,Status\n")

    for w in state['zp']['wards']:
        output.append(f"ZP,{w['blockName']},{w['wardNo']},\"{w['winner']['name']}\",{w['winner']['party']},{w['winner']['totalVotes']},\"{w['runnerUp']['name']}\",{w['runnerUp']['party']},{w['runnerUp']['totalVotes']},{w['margin']},{w['status']}\n")

    for w in state['ps']['wards']:
        output.append(f"PS,{w['blockName']},{w['wardNo']},\"{w['winner']['name']}\",{w['winner']['party']},{w['winner']['totalVotes']},\"{w['runnerUp']['name']}\",{w['runnerUp']['party']},{w['runnerUp']['totalVotes']},{w['margin']},{w['status']}\n")

    csv_text = "".join(output)
    return Response(content=csv_text, media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename=salumber_election_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    })

# ==============================================================================
# HTML ROUTES
# ==============================================================================
@app.get("/", response_class=HTMLResponse)
def serve_tv_display():
    """Serves the pure 50/50 live broadcast display for big TV screens."""
    if os.path.exists("public/index.html"):
        return FileResponse("public/index.html")
    elif os.path.exists("index.html"):
        return FileResponse("index.html")
    return "<h1>TV Display not found</h1>"

@app.get("/entry", response_class=HTMLResponse)
def serve_entry_console():
    """Serves the mobile & desktop vote entry console for operators."""
    if os.path.exists("public/entry.html"):
        return FileResponse("public/entry.html")
    return "<h1>Entry console not found</h1>"

@app.get("/admin", response_class=HTMLResponse)
def serve_admin():
    """Serves admin console for candidate management and exports."""
    if os.path.exists("public/admin.html"):
        return FileResponse("public/admin.html")
    return FileResponse("public/entry.html")

if __name__ == "__main__":
    print("=" * 70)
    print("   SALUMBER LIVE ELECTION PORTAL & DATABASE SERVER")
    print("=" * 70)
    print("   TV Broadcast Screen : http://localhost:8000/")
    print("   Operator Vote Entry : http://localhost:8000/entry")
    print("   Admin & Candidates  : http://localhost:8000/admin")
    print("=" * 70)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
