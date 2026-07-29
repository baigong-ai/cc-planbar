#!/bin/bash
# Inject statusLine into CC Switch's common config snapshot,
# so switching providers no longer drops the statusline.
set -e
DB="$HOME/.cc-switch/cc-switch.db"
[ -f "$DB" ] || { echo "CC Switch db not found, skip"; exit 0; }
cp "$DB" "$DB.bak-statusline"
python3 -c "
import sqlite3, json
db = sqlite3.connect('$DB')
row = db.execute(\"SELECT value FROM settings WHERE key='common_config_claude'\").fetchone()
if not row:
    print('common_config_claude not found, skip')
else:
    v = json.loads(row[0])
    v['statusLine'] = {'type': 'command', 'command': 'ccstatusline'}
    db.execute(\"UPDATE settings SET value=? WHERE key='common_config_claude'\",
               (json.dumps(v, ensure_ascii=False, indent=2),))
    db.commit()
    print('statusLine injected into common_config_claude')
"
