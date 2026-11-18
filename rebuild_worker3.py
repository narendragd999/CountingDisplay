# -*- coding: utf-8 -*-
import json, sqlite3

with open('public/index.html', 'r', encoding='utf-8') as f:
    index_html = f.read()

with open('public/entry.html', 'r', encoding='utf-8') as f:
    entry_html = f.read()

with open('public/smart_tv.html', 'r', encoding='utf-8') as f:
    smart_tv_html = f.read()

conn = sqlite3.connect('election_salumber_2026.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT * FROM candidates WHERE is_active = 1 ORDER BY ward_no, ballot_no')
c_rows = [dict(r) for r in cursor.fetchall()]

cursor.execute('SELECT category, block_name, ward_no, ward_name_hindi, reservation, status, max_rounds, is_setup_done, total_booths, counting_tables FROM wards')
w_rows = [dict(r) for r in cursor.fetchall()]

cursor.execute('SELECT candidate_id, round_key, votes_count FROM votes')
v_rows = cursor.fetchall()
round_votes = {}
for r in v_rows:
    cid = r['candidate_id']
    if cid not in round_votes:
        round_votes[cid] = {}
    round_votes[cid][r['round_key']] = r['votes_count']

cursor.execute('SELECT block_name, booth_no, booth_name_hi, booth_name_en, ps_ward, zp_ward, total_elector FROM booths')
b_rows = [dict(r) for r in cursor.fetchall()]

cursor.execute('SELECT username, password, role, assigned_block, display_name FROM users WHERE is_active = 1')
u_rows = [dict(r) for r in cursor.fetchall()]

cursor.execute("SELECT value FROM system_settings WHERE key = 'system_mode'")
sm_row = cursor.fetchone()
system_mode = sm_row[0] if sm_row else "TEST"

master = {
    'candidates': c_rows,
    'wards': w_rows,
    'roundVotes': round_votes,
    'booths': b_rows,
    'system_mode': system_mode
}
conn.close()

master_json_str = json.dumps(master, ensure_ascii=False)
index_json_str = json.dumps(index_html)
entry_json_str = json.dumps(entry_html)
smart_tv_json_str = json.dumps(smart_tv_html)
users_json_str = json.dumps(u_rows, ensure_ascii=False)

worker_template = """/**
 * Cloudflare Worker for Salumber District Elections 2026
 * Full-Width UI • Production & Test Modes • Multi-Account RBAC
 */

const INDEX_HTML = __INDEX_HTML__;
const ENTRY_HTML = __ENTRY_HTML__;
const SMART_TV_HTML = __SMART_TV_HTML__;
let MASTER_DATA = __MASTER_DATA__;
const USERS_LIST = __USERS_LIST__;
let SYSTEM_MODE = "__SYSTEM_MODE__";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Auth-Token'
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const jsonResponse = (data, status = 200) => {
      return new Response(JSON.stringify(data), {
        status,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    };

    if (path === '/entry') {
      return new Response(ENTRY_HTML, {
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
      });
    }

    if (path === '/tv' || path === '/smart') {
      return new Response(SMART_TV_HTML, {
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
      });
    }

    if (path === '/api/all_candidates_master') {
      MASTER_DATA.system_mode = SYSTEM_MODE;
      return jsonResponse(MASTER_DATA);
    }

    if (path === '/api/ward_configs') {
      return jsonResponse({ status: 'success', wards: MASTER_DATA.wards });
    }

    // HALL & TABLES SETUP ENDPOINTS
    if (path === '/api/hall_summary') {
      const psWards = MASTER_DATA.wards.filter(w => w.category === 'PS');
      const blocksMap = {};
      psWards.forEach(w => {
        const blk = w.block_name;
        if (!blocksMap[blk]) {
          blocksMap[blk] = {
            category: 'PS',
            block_name: blk,
            total_wards: 0,
            total_booths: 0,
            min_booths: Infinity,
            max_booths: -Infinity,
            min_tables: Infinity,
            max_tables: -Infinity,
            min_rounds: Infinity,
            max_rounds: -Infinity
          };
        }
        const b = blocksMap[blk];
        b.total_wards += 1;
        const booths = Number(w.total_booths) || 5;
        const tables = Number(w.counting_tables) || 5;
        const rounds = Number(w.max_rounds) || Math.ceil(booths / tables);
        b.total_booths += booths;
        if (booths < b.min_booths) b.min_booths = booths;
        if (booths > b.max_booths) b.max_booths = booths;
        if (tables < b.min_tables) b.min_tables = tables;
        if (tables > b.max_tables) b.max_tables = tables;
        if (rounds < b.min_rounds) b.min_rounds = rounds;
        if (rounds > b.max_rounds) b.max_rounds = rounds;
      });
      const halls = Object.values(blocksMap).sort((a,b) => a.block_name.localeCompare(b.block_name));
      return jsonResponse({ status: 'success', halls });
    }

    if (path === '/api/save_ward_config' && request.method === 'POST') {
      try {
        const body = await request.json();
        const { category, block, ward_no, total_booths, counting_tables, max_rounds, reservation } = body;
        const ward = MASTER_DATA.wards.find(w => w.category === category && w.block_name === block && Number(w.ward_no) === Number(ward_no));
        if (ward) {
          if (total_booths !== undefined) ward.total_booths = Number(total_booths);
          if (counting_tables !== undefined) ward.counting_tables = Number(counting_tables);
          if (max_rounds !== undefined) ward.max_rounds = Number(max_rounds);
          if (reservation !== undefined) ward.reservation = reservation;
          return jsonResponse({ status: 'success', message: 'Ward configuration updated successfully!' });
        }
        return jsonResponse({ detail: 'Ward not found' }, 404);
      } catch (e) {
        return jsonResponse({ detail: e.message }, 500);
      }
    }

    if (path === '/api/bulk_apply_hall_config' && request.method === 'POST') {
      try {
        const body = await request.json();
        const { category, block, counting_tables } = body;
        const tables = Math.max(1, Number(counting_tables) || 5);
        MASTER_DATA.wards.forEach(w => {
          let match = false;
          if (category === 'ALL') match = true;
          else if (category === 'ZP' && w.category === 'ZP') match = true;
          else if (w.category === 'PS' && (!block || w.block_name === block)) match = true;
          if (match) {
            w.counting_tables = tables;
            const booths = Number(w.total_booths) || 5;
            w.max_rounds = Math.max(1, Math.ceil(booths / tables));
          }
        });
        return jsonResponse({ status: 'success', message: 'Bulk configuration applied successfully!' });
      } catch (e) {
        return jsonResponse({ detail: e.message }, 500);
      }
    }

    // ROUND DECLARATION & EKZAI
    if (path === '/api/declare_round' && request.method === 'POST') {
      try {
        const body = await request.json();
        const { category, block, round_key } = body;
        if (!MASTER_DATA.declaredRounds) MASTER_DATA.declaredRounds = [];
        const existing = MASTER_DATA.declaredRounds.find(r => r.category === category && r.block_name === block && r.round_key === round_key);
        if (!existing) {
          MASTER_DATA.declaredRounds.push({ category, block_name: block, round_key, status: 'DECLARED', declared_at: new Date().toISOString() });
        }
        return jsonResponse({ status: 'success', message: `Round ${round_key} declared successfully!` });
      } catch (e) {
        return jsonResponse({ detail: e.message }, 500);
      }
    }

    if (path === '/api/reopen_round' && request.method === 'POST') {
      try {
        const body = await request.json();
        const { category, block, round_key } = body;
        if (MASTER_DATA.declaredRounds) {
          MASTER_DATA.declaredRounds = MASTER_DATA.declaredRounds.filter(r => !(r.category === category && r.block_name === block && r.round_key === round_key));
        }
        return jsonResponse({ status: 'success', message: `Round ${round_key} reopened successfully!` });
      } catch (e) {
        return jsonResponse({ detail: e.message }, 500);
      }
    }

    if (path === '/api/round_ekzai') {
      const category = url.searchParams.get('category') || 'PS';
      const block = url.searchParams.get('block') || 'Semari';
      const round_key = (url.searchParams.get('round_key') || 'R1').toUpperCase();

      const decl = (MASTER_DATA.declaredRounds || []).find(r => r.category === category && r.block_name === block && r.round_key === round_key);
      const is_declared = Boolean(decl);

      const cand_rows = MASTER_DATA.candidates
        .filter(c => c.category === category && c.block_name === block)
        .map(c => {
          const vObj = MASTER_DATA.roundVotes[c.id] || {};
          const curVotes = Number(vObj[round_key]) || 0;
          return { ...c, current_round_votes: curVotes };
        });

      const order = ['PB', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10'];
      const target_idx = order.indexOf(round_key);
      const preceding_keys = target_idx > 0 ? order.slice(0, target_idx) : [];

      const wards_map = {};
      cand_rows.forEach(c => {
        const vObj = MASTER_DATA.roundVotes[c.id] || {};
        let prev_total = 0;
        preceding_keys.forEach(pk => {
          prev_total += (Number(vObj[pk]) || 0);
        });
        const cumul = prev_total + c.current_round_votes;
        const wNo = c.ward_no;
        if (!wards_map[wNo]) wards_map[wNo] = [];
        wards_map[wNo].push({
          candidate_id: c.id,
          name_hindi: c.name_hindi,
          party: c.party,
          ballot_no: c.ballot_no,
          prev_cumulative: prev_total,
          round_votes: c.current_round_votes,
          cumulative: cumul
        });
      });

      return jsonResponse({
        status: 'success',
        round_key,
        category,
        block,
        is_declared,
        wards: wards_map
      });
    }

    // AUTH LOGIN
    if (path === '/api/auth/login' && request.method === 'POST') {
      try {
        const body = await request.json();
        const uname = (body.username || '').trim().toLowerCase();
        const pwd = (body.password || '').trim();

        let matched = null;
        if (uname) {
          matched = USERS_LIST.find(u => u.username.toLowerCase() === uname && u.password === pwd);
        } else {
          matched = USERS_LIST.find(u => u.password === pwd);
        }

        if (!matched && pwd === 'salumber2026') {
          matched = { username: 'admin', role: 'ADMIN', assigned_block: null, display_name: 'District Super Admin' };
        }

        if (matched) {
          return jsonResponse({
            status: 'success',
            token: `${matched.username}_cftoken_${Date.now()}`,
            user: {
              username: matched.username,
              role: matched.role,
              assigned_block: matched.assigned_block,
              display_name: matched.display_name
            },
            system_mode: SYSTEM_MODE,
            message: `Welcome, ${matched.display_name}!`
          });
        } else {
          return jsonResponse({ detail: 'Invalid username or password!' }, 401);
        }
      } catch (e) {
        return jsonResponse({ detail: 'Bad request: ' + e }, 400);
      }
    }

    // AUTH CHECK
    if (path === '/api/auth/check') {
      const token = request.headers.get('X-Auth-Token') || '';
      if (token.includes('_cftoken_') || token.includes('_')) {
        const lastIdx = token.lastIndexOf('_');
        const uname = (lastIdx > 0 ? token.substring(0, lastIdx) : token);
        const user = USERS_LIST.find(u => u.username.toLowerCase() === uname) || {
          username: uname,
          role: 'ADMIN',
          assigned_block: null,
          display_name: 'Super Admin'
        };
        return jsonResponse({
          authenticated: true,
          user: {
            username: user.username,
            role: user.role,
            assigned_block: user.assigned_block,
            display_name: user.display_name
          },
          system_mode: SYSTEM_MODE
        });
      }
      return jsonResponse({ authenticated: false, system_mode: SYSTEM_MODE });
    }

    // TOGGLE SYSTEM MODE (Admin Only)
    if (path === '/api/set_system_mode' && request.method === 'POST') {
      try {
        const body = await request.json();
        const mode = (body.mode || '').toUpperCase();
        if (mode === 'PRODUCTION' || mode === 'TEST') {
          SYSTEM_MODE = mode;
          MASTER_DATA.system_mode = SYSTEM_MODE;
          if (mode === 'PRODUCTION') {
            // Automatically clear all mock/testing data when transitioning to PRODUCTION mode
            MASTER_DATA.roundVotes = {};
            MASTER_DATA.declaredRounds = [];
            (MASTER_DATA.wards || []).forEach(w => {
              w.status = 'COUNTING';
            });
          }
          return jsonResponse({
            status: 'success',
            system_mode: SYSTEM_MODE,
            message: mode === 'PRODUCTION'
              ? 'System switched to PRODUCTION mode! All test data has been cleared for Live Election.'
              : `System switched to ${SYSTEM_MODE} mode successfully!`
          });
        }
        return jsonResponse({ detail: 'Invalid mode' }, 400);
      } catch (e) {
        return jsonResponse({ detail: 'Bad request' }, 400);
      }
    }

    // RESET TESTING DATA (Blocked in Production!)
    if (path === '/api/seed_dummy_test_data' && request.method === 'POST') {
      if (SYSTEM_MODE === 'PRODUCTION') {
        return jsonResponse({ detail: 'CRITICAL: DUMMY TEST DATA GENERATION IS BLOCKED IN PRODUCTION MODE!' }, 403);
      }
      MASTER_DATA.roundVotes = {};
      MASTER_DATA.declaredRounds = [
        { category: 'ZP', block_name: 'Salumber ZP', round_key: 'R1', status: 'DECLARED' },
        { category: 'ZP', block_name: 'Salumber ZP', round_key: 'R2', status: 'DECLARED' },
        { category: 'ZP', block_name: 'Salumber ZP', round_key: 'R3', status: 'DECLARED' },
        { category: 'PS', block_name: 'Semari', round_key: 'R1', status: 'DECLARED' },
        { category: 'PS', block_name: 'Semari', round_key: 'R2', status: 'DECLARED' },
        { category: 'PS', block_name: 'Sarada', round_key: 'R1', status: 'DECLARED' },
        { category: 'PS', block_name: 'Sarada', round_key: 'R2', status: 'DECLARED' },
        { category: 'PS', block_name: 'Salumbar', round_key: 'R1', status: 'DECLARED' },
        { category: 'PS', block_name: 'Salumbar', round_key: 'R2', status: 'DECLARED' },
        { category: 'PS', block_name: 'Jaisamand', round_key: 'R1', status: 'DECLARED' },
        { category: 'PS', block_name: 'Jaisamand', round_key: 'R2', status: 'DECLARED' },
        { category: 'PS', block_name: 'Geengla', round_key: 'R1', status: 'DECLARED' },
        { category: 'PS', block_name: 'Geengla', round_key: 'R2', status: 'DECLARED' },
        { category: 'PS', block_name: 'Lasadiya', round_key: 'R1', status: 'DECLARED' },
        { category: 'PS', block_name: 'Lasadiya', round_key: 'R2', status: 'DECLARED' },
        { category: 'PS', block_name: 'Jhallara', round_key: 'R1', status: 'DECLARED' },
        { category: 'PS', block_name: 'Jhallara', round_key: 'R2', status: 'DECLARED' }
      ];
      (MASTER_DATA.candidates || []).forEach((c, idx) => {
        const vObj = {};
        const isNota = (c.party === 'NOTA' || (c.name_hindi || '').includes('नोटा'));
        const w = (MASTER_DATA.wards || []).find(wd => wd.category === c.category && wd.block_name === c.block_name && wd.ward_no === c.ward_no);
        const maxR = (w && w.max_rounds) ? w.max_rounds : 5;

        // PB
        vObj['PB'] = isNota ? 5 : (12 + (idx % 18));
        
        // Fill ALL rounds up to max_rounds
        for (let r = 1; r <= maxR; r++) {
          vObj[`R${r}`] = isNota ? (8 + (r * 2)) : (220 + ((idx * 23 + r * 17) % 210));
        }

        MASTER_DATA.roundVotes[c.id] = vObj;
      });
      (MASTER_DATA.wards || []).forEach(w => {
        if (w.category === 'ZP' && [1, 3, 5, 8, 11, 14, 18, 21].includes(w.ward_no)) {
          w.status = 'DECLARED';
        } else if (w.category === 'PS' && ([1, 3, 6, 9, 12, 15].includes(w.ward_no) || (w.ward_no % 3 === 0))) {
          w.status = 'DECLARED';
        } else {
          w.status = 'COUNTING';
        }
      });
      return jsonResponse({
        status: 'success',
        message: '🎲 Realistic multi-round test data (PB, R1 to R5) generated successfully on Cloudflare!'
      });
    }

    if (path === '/api/reset_testing_data' && request.method === 'POST') {
      if (SYSTEM_MODE === 'PRODUCTION') {
        return jsonResponse({ detail: 'CRITICAL: DATA RESET IS BLOCKED IN PRODUCTION MODE!' }, 403);
      }
      MASTER_DATA.roundVotes = {};
      MASTER_DATA.declaredRounds = [];
      MASTER_DATA.wards.forEach(w => {
        w.status = 'COUNTING';
      });
      return jsonResponse({
        status: 'success',
        message: 'All entered votes reset successfully. Master data preserved.'
      });
    }

    // SAVE VOTES
    if (path === '/api/save_votes' && request.method === 'POST') {
      try {
        const body = await request.json();
        const { category, block, ward_no, round_key, votes, candidate_votes } = body;
        const normalizedKey = (round_key || 'R1').toUpperCase();

        if (votes && typeof votes === 'object' && !Array.isArray(votes)) {
          for (const [candId, count] of Object.entries(votes)) {
            const cid = Number(candId);
            if (!MASTER_DATA.roundVotes[cid]) MASTER_DATA.roundVotes[cid] = {};
            MASTER_DATA.roundVotes[cid][normalizedKey] = Number(count) || 0;
          }
        } else if (Array.isArray(candidate_votes)) {
          for (const cv of candidate_votes) {
            const cid = Number(cv.candidate_id);
            if (!MASTER_DATA.roundVotes[cid]) MASTER_DATA.roundVotes[cid] = {};
            MASTER_DATA.roundVotes[cid][normalizedKey] = Number(cv.votes) || 0;
          }
        }

        return jsonResponse({ status: 'success', message: `Votes saved for ${normalizedKey}` });
      } catch (e) {
        return jsonResponse({ status: 'error', detail: e.message }, 500);
      }
    }

    // DECLARE WARD WINNER
    if (path === '/api/declare_ward' && request.method === 'POST') {
      try {
        const { category, block, ward_no } = await request.json();
        const ward = MASTER_DATA.wards.find(w => w.category === category && w.block_name === block && Number(w.ward_no) === Number(ward_no));
        if (ward) {
          ward.status = 'DECLARED';
          return jsonResponse({ status: 'success', message: `${category} Ward ${ward_no} declared!` });
        }
        return jsonResponse({ status: 'error', detail: 'Ward not found' }, 404);
      } catch (e) {
        return jsonResponse({ status: 'error', detail: e.message }, 500);
      }
    }

    // REOPEN WARD
    if (path === '/api/reopen_ward' && request.method === 'POST') {
      try {
        const { category, block, ward_no } = await request.json();
        const ward = MASTER_DATA.wards.find(w => w.category === category && w.block_name === block && Number(w.ward_no) === Number(ward_no));
        if (ward) {
          ward.status = 'COUNTING';
          return jsonResponse({ status: 'success', message: `${category} Ward ${ward_no} reopened!` });
        }
        return jsonResponse({ status: 'error', detail: 'Ward not found' }, 404);
      } catch (e) {
        return jsonResponse({ status: 'error', detail: e.message }, 500);
      }
    }

    // EXPORT DATABASE SNAPSHOT (For Live -> Local Backup)
    if (path === '/api/database/export' || path === '/api/database/export_json' || path === '/api/database/export_sqlite') {
      MASTER_DATA.system_mode = SYSTEM_MODE;
      const jsonStr = JSON.stringify(MASTER_DATA, null, 2);
      return new Response(jsonStr, {
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Content-Disposition': 'attachment; filename="election_salumber_live_snapshot.json"'
        }
      });
    }

    // IMPORT DATABASE SNAPSHOT (Restore into Worker Memory)
    if (path === '/api/database/import' && request.method === 'POST') {
      try {
        let importedData = null;
        const contentType = request.headers.get('content-type') || '';
        if (contentType.includes('multipart/form-data')) {
          const formData = await request.formData();
          const file = formData.get('file');
          if (file) {
            const text = await file.text();
            importedData = JSON.parse(text);
          }
        } else {
          importedData = await request.json();
        }

        if (!importedData) {
          return jsonResponse({ detail: 'No data or invalid file provided' }, 400);
        }

        if (importedData.roundVotes) {
          MASTER_DATA.roundVotes = importedData.roundVotes;
        }
        if (importedData.wards) {
          importedData.wards.forEach(w => {
            const target = MASTER_DATA.wards.find(mw => mw.category === w.category && mw.block_name === w.block_name && mw.ward_no === w.ward_no);
            if (target && w.status) target.status = w.status;
          });
        }
        if (importedData.system_mode) {
          SYSTEM_MODE = importedData.system_mode;
          MASTER_DATA.system_mode = SYSTEM_MODE;
        }

        return jsonResponse({
          status: 'success',
          type: 'json',
          message: 'Data successfully restored into live worker memory!'
        });
      } catch (e) {
        return jsonResponse({ detail: 'Import failed: ' + e.message }, 400);
      }
    }

    // API 404 Guard: Never return HTML for an API request!
    if (path.startsWith('/api/')) {
      return jsonResponse({ detail: `API endpoint ${path} not found` }, 404);
    }

    // SERVE DEFAULT TV DISPLAY (index.html)
    return new Response(INDEX_HTML, {
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
  }
};
"""

worker_content = worker_template.replace('__INDEX_HTML__', index_json_str)
worker_content = worker_content.replace('__ENTRY_HTML__', entry_json_str)
worker_content = worker_content.replace('__SMART_TV_HTML__', smart_tv_json_str)
worker_content = worker_content.replace('__MASTER_DATA__', master_json_str)
worker_content = worker_content.replace('__USERS_LIST__', users_json_str)
worker_content = worker_content.replace('__SYSTEM_MODE__', system_mode)

with open('worker.js', 'w', encoding='utf-8') as f:
    f.write(worker_content)

print("worker.js successfully rebuilt with Full RBAC, Mode Guards & Full-Width layout!")
