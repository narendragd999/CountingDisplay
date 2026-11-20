import re

with open('public/entry.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Export DB button to open modal
content = content.replace(
    '''<button id="btnExportDb" onclick="exportDatabase()" class="btn btn-outline" style="color:#0f766e; border-color:#99f6e4; background:#f0fdfa; font-weight:800; font-size:12px;" title="Download complete database backup (.db file) to local computer">
          💾 Export DB
        </button>''',
    '''<button id="btnExportDb" onclick="openExportDbModal()" class="btn btn-outline" style="color:#0f766e; border-color:#99f6e4; background:#f0fdfa; font-weight:800; font-size:12px;" title="Download complete database backup (.json or .db)">
          💾 Export DB
        </button>'''
)

# 2. Add Export DB Modal before importDbModal
export_modal_html = '''  <!-- EXPORT DATABASE MODAL -->
  <div id="exportDbModal" class="modal-backdrop" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.55); z-index:9999; align-items:center; justify-content:center;">
    <div style="background:#ffffff; border-radius:12px; width:90%; max-width:540px; box-shadow:var(--shadow-lg); overflow:hidden; border:1px solid var(--border-main);">
      <div style="padding:16px 20px; background:#0f766e; color:#ffffff; display:flex; justify-content:space-between; align-items:center;">
        <div style="font-size:15px; font-weight:800; display:flex; align-items:center; gap:8px;">
          <span>💾</span> Export Database & Sync Backup
        </div>
        <button type="button" onclick="closeExportDbModal()" style="background:transparent; border:none; color:#cbd5e1; font-size:18px; cursor:pointer; font-weight:bold;">✕</button>
      </div>

      <div style="padding:20px; display:flex; flex-direction:column; gap:14px;">
        <div style="background:#f0fdfa; border:1px solid #99f6e4; border-radius:8px; padding:12px 14px; font-size:12.5px; color:#115e59; line-height:1.5;">
          <strong>बैकअप का प्रारूप चुनें (Select Export Format):</strong>
        </div>

        <!-- Option 1: JSON Snapshot for Live Cloudflare -->
        <div onclick="downloadBackupFormat('json')" style="border:2px solid #0d9488; background:#f0fdfa; border-radius:10px; padding:14px; cursor:pointer; transition:all 0.15s ease;">
          <div style="font-size:14px; font-weight:800; color:#0f766e; display:flex; align-items:center; justify-content:space-between;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span>☁️</span> Portable JSON Snapshot (.json)
            </div>
            <span style="background:#0d9488; color:#fff; font-size:10.5px; padding:2px 8px; border-radius:4px; font-weight:700;">FOR LIVE CLOUDFLARE</span>
          </div>
          <div style="font-size:12px; color:#334155; margin-top:6px; line-height:1.4;">
            यह फ़ाइल <strong>Live Cloudflare Worker (countingdisplay...workers.dev) पर सीधे इम्पोर्ट</strong> करने और मल्टी-सिस्टम सिंक के लिए 100% अनुकूल है।
          </div>
        </div>

        <!-- Option 2: SQLite .db for local -->
        <div onclick="downloadBackupFormat('sqlite')" style="border:1px solid #cbd5e1; background:#f8fafc; border-radius:10px; padding:14px; cursor:pointer; transition:all 0.15s ease;">
          <div style="font-size:14px; font-weight:800; color:#334155; display:flex; align-items:center; justify-content:space-between;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span>💾</span> Full SQLite Database (.db)
            </div>
            <span style="background:#64748b; color:#fff; font-size:10.5px; padding:2px 8px; border-radius:4px; font-weight:700;">LOCAL ONLY</span>
          </div>
          <div style="font-size:12px; color:#64748b; margin-top:6px; line-height:1.4;">
            लोकल कंप्यूटर के SQLite डेटाबेस का संपूर्ण बाइनरी बैकअप (.db फ़ाइल)।
          </div>
        </div>

        <div style="display:flex; justify-content:flex-end; margin-top:6px;">
          <button type="button" onclick="closeExportDbModal()" class="btn btn-outline" style="padding:8px 16px; font-weight:700;">
            रद्द करें (Cancel)
          </button>
        </div>
      </div>
    </div>
  </div>\n\n'''

content = content.replace('  <!-- IMPORT DATABASE MODAL (FAILSAFE RESTORE) -->', export_modal_html + '  <!-- IMPORT DATABASE MODAL (FAILSAFE RESTORE) -->')

# 3. Update description inside importDbModal
content = content.replace(
    '<div style="font-size:11px; color:var(--text-muted); margin-top:4px;">Accepts <code>.db</code> (SQLite database) or <code>.json</code> (snapshot)</div>',
    '<div style="font-size:11.5px; color:#475569; margin-top:6px; line-height:1.4;"><strong>☁️ Live Cloudflare पर:</strong> केवल <code>.json</code> Snapshot फ़ाइल चुनें (जैसे <code>election_salumber_latest_snapshot.json</code>)<br><strong>💻 Localhost पर:</strong> <code>.json</code> एवं <code>.db</code> दोनों समर्थित हैं</div>'
)

# 4. Update JavaScript export/import handlers
old_js = '''    function exportDatabase() {
      // Direct native browser download with auth token
      const url = '/api/database/export?token=' + encodeURIComponent(authToken);
      showToast('⏳ Downloading database backup...');
      const a = document.createElement('a');
      a.href = url;
      a.download = '';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }'''

new_js = '''    function openExportDbModal() {
      const modal = document.getElementById('exportDbModal');
      if (modal) modal.style.display = 'flex';
    }

    function closeExportDbModal() {
      const modal = document.getElementById('exportDbModal');
      if (modal) modal.style.display = 'none';
    }

    function downloadBackupFormat(fmt) {
      closeExportDbModal();
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      let endpoint = '/api/database/export_json';
      if (fmt === 'sqlite') {
        if (!isLocal) {
          alert('⚠️ SQLite (.db) फ़ाइल केवल लोकल सर्वर पर उपलब्ध है। Live Cloudflare के लिए JSON Snapshot डाउनलोड किया जा रहा है।');
        } else {
          endpoint = '/api/database/export_sqlite';
        }
      }
      const url = endpoint + '?token=' + encodeURIComponent(authToken);
      showToast('⏳ Downloading ' + (fmt === 'sqlite' && isLocal ? 'SQLite Database (.db)' : 'Live Snapshot (.json)') + '...');
      const a = document.createElement('a');
      a.href = url;
      a.download = '';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    function exportDatabase() {
      openExportDbModal();
    }'''

content = content.replace(old_js, new_js)

# 5. Add check in submitDatabaseImport
old_submit = '''      const file = input.files[0];
      const confirmed = confirm(`Are you sure you want to restore database from "${file.name}"?\\n\\nThis will update vote tallies and ward statuses to match the backup file. Proceed?`);
      if (!confirmed) return;'''

new_submit = '''      const file = input.files[0];
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      if (!isLocal && (file.name.toLowerCase().endsWith('.db') || file.name.toLowerCase().endsWith('.sqlite') || file.name.toLowerCase().endsWith('.sqlite3'))) {
        alert('⚠️ ध्यान दें (Cloudflare Workers Error):\n\nCloudflare Worker केवल Portable JSON Snapshot (.json) स्वीकार करता है।\\n\\nकृपया अपने लोकल कंप्यूटर से Export की गई ".json" Snapshot फ़ाइल चुनें (जैसे election_salumber_latest_snapshot.json)।\\n\\n.db फ़ाइल सिर्फ लोकल सर्वर के लिए होती है।');
        return;
      }

      const confirmed = confirm(`Are you sure you want to restore database from "${file.name}"?\\n\\nThis will update vote tallies and ward statuses to match the backup file. Proceed?`);
      if (!confirmed) return;'''

content = content.replace(old_submit, new_submit)

with open('public/entry.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("public/entry.html successfully updated!")
