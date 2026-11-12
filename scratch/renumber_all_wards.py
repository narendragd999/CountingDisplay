# -*- coding: utf-8 -*-
"""
Re-number ALL wards across ALL blocks using official ballot order:
  1. State Party candidates (BJP, INC, BAP, AAP, etc.) → Hindi A-Z
  2. Independent (IND / निर्दलीय)                      → Hindi A-Z
  3. NOTA                                               → last
"""
import sqlite3
import unicodedata
import json

# ── Official recognized / state / national party codes ──────────────────
# Anything NOT in this set (and not NOTA) is treated as Independent.
STATE_PARTIES = {
    'BJP',      # Bharatiya Janata Party
    'INC',      # Indian National Congress
    'BSP',      # Bahujan Samaj Party
    'CPIM',     # Communist Party of India (Marxist)
    'CPI(M)',
    'CPI-M',
    'CPI_M',
    'AAP',      # Aam Aadmi Party
    'NPP',      # National People's Party
    'BAP',      # Bhartiya Aadiwasi Party
}

def is_nota(name, party):
    return (party or '').upper() == 'NOTA' or 'नोटा' in (name or '')

def is_ind(party):
    return (party or '').strip().upper() not in STATE_PARTIES

def clean_hi(name):
    if not name:
        return ""
    return unicodedata.normalize('NFKC', name).strip().strip('\u200b\u200c\u200d\ufeff\xa0')

conn = sqlite3.connect('election_salumber_2026.db')
cursor = conn.cursor()

# Get all distinct wards
cursor.execute("SELECT DISTINCT category, block_name, ward_no FROM candidates WHERE is_active=1 ORDER BY category, block_name, ward_no")
wards = cursor.fetchall()
print(f"Total wards to re-number: {len(wards)}")

done = 0
errors = 0

for cat, blk, wno in wards:
    try:
        cursor.execute(
            "SELECT id, name_hindi, party FROM candidates WHERE category=? AND block_name=? AND ward_no=? AND is_active=1",
            (cat, blk, wno)
        )
        rows = cursor.fetchall()

        state_party = []
        independent = []
        nota = []

        for cid, name, party in rows:
            if is_nota(name, party):
                nota.append((cid, name, party))
            elif is_ind(party):
                independent.append((cid, name, party))
            else:
                state_party.append((cid, name, party))

        state_party_sorted = sorted(state_party, key=lambda x: clean_hi(x[1]))
        independent_sorted = sorted(independent, key=lambda x: clean_hi(x[1]))
        ordered = state_party_sorted + independent_sorted + nota

        for seq, (cid, cname, cparty) in enumerate(ordered, start=1):
            cursor.execute("UPDATE candidates SET ballot_no = ? WHERE id = ?", (seq, cid))

        done += 1
        # Print summary for wards that have mixed state+IND
        if state_party and independent:
            last_state = state_party_sorted[-1][1]
            first_ind   = independent_sorted[0][1]
            print(f"  {cat} {blk} W{wno}: {len(state_party_sorted)} state({last_state[:8]}...) | {len(independent_sorted)} IND({first_ind[:8]}...) | {len(nota)} NOTA")

    except Exception as e:
        print(f"  ERROR {cat} {blk} W{wno}: {e}")
        errors += 1

conn.commit()

# Sync all_candidates_master.json
cursor.execute("""
    SELECT id, category, block_name, ward_no, ballot_no, name_hindi, party, symbol, gender, age, candidate_category
    FROM candidates ORDER BY category, block_name, ward_no, ballot_no
""")
cols = [d[0] for d in cursor.description]
all_cands = [dict(zip(cols, row)) for row in cursor.fetchall()]
with open('all_candidates_master.json', 'w', encoding='utf-8') as f:
    json.dump(all_cands, f, ensure_ascii=False, indent=2)

conn.close()
print(f"\nDone: {done} wards re-numbered, {errors} errors.")
print("all_candidates_master.json synced.")
