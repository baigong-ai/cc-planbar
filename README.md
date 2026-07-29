# cc-planbar

[中文](README_CN.md)

A Claude Code statusline widget showing quota for third-party coding plan providers (Kimi, Zhipu GLM, etc.).

Shows in the statusline: **context window usage % + current provider's plan quota** (5-hour window / weekly limit, with reset times), color-coded by usage: green <60%, yellow 60–84%, red ≥85%.

```
Model: k3 | Ctx 24.0% | Kimi 5h 15% (rst 03:44) · week 69% (rst 07/31 05:44)
```

Quota queries follow CC Switch's implementation, with the provider auto-detected from `ANTHROPIC_BASE_URL`:

| base_url contains | provider | endpoint |
|---|---|---|
| `api.kimi.com/coding` | Kimi | `GET /coding/v1/usages` (Bearer auth) |
| `bigmodel.cn` / `api.z.ai` | Zhipu GLM | `GET /api/monitor/usage/quota/limit` (raw key, no Bearer prefix) |

The quota endpoint is polled at most once every 5 minutes (cached); switching providers invalidates the old cache automatically.

## Requirements & Scope

- **Required**: Claude Code + Node.js. Rendering is done by [ccstatusline](https://github.com/sirmalloc/ccstatusline) — cc-planbar runs as its custom-command widget
- **For**: users on third-party coding plan providers via `ANTHROPIC_BASE_URL` (built-in support for Kimi For Coding and Zhipu GLM, both bigmodel.cn and z.ai; other providers can be added quickly by writing a function like `zhipu()` and registering it in `PROVIDERS`). Works however you switch providers — CC Switch, manual edits, or any other tool — as long as the base URL in `~/.claude/settings.json` points to a supported provider
- **Optional**: `fix-cc-switch.sh` is only needed if you switch providers with [CC Switch](https://github.com/farion1231/cc-switch); ignore it otherwise

## Files

| file | install to |
|---|---|
| `quota-status.py` | `~/.claude/scripts/quota-status.py` |
| `ccstatusline-settings.json` | `~/.config/ccstatusline/settings.json` |
| `fix-cc-switch.sh` | only needed if you use CC Switch; run once |

## Installation

```bash
# 1. Install the statusline renderer (requires Node.js)
npm install -g ccstatusline

# 2. Copy files
mkdir -p ~/.claude/scripts ~/.config/ccstatusline
cp quota-status.py ~/.claude/scripts/
cp ccstatusline-settings.json ~/.config/ccstatusline/settings.json
chmod +x ~/.claude/scripts/quota-status.py
```

Then edit `~/.claude/settings.json` and add at the top level:

```json
"statusLine": {
  "type": "command",
  "command": "ccstatusline"
}
```

Restart Claude Code to apply.

## If you switch providers with CC Switch

When switching, CC Switch rewrites `~/.claude/settings.json` as "provider env + common config snapshot". If that snapshot has no `statusLine`, the statusline disappears. Run the fix script once (it injects `statusLine` into the snapshot):

```bash
bash fix-cc-switch.sh
```

Then **restart the CC Switch app** before switching providers.

## FAQ

**Will a CC Switch upgrade break the fix-cc-switch.sh patch?**

No, for two reasons:

1. The fix writes to CC Switch's user data directory (`~/.cc-switch/cc-switch.db`). App upgrades only replace the application binary — they don't touch the database or re-run completed migrations
2. Even if CC Switch later re-captures the common config snapshot from the live `settings.json`, the captured snapshot will include `statusLine` as long as your live `settings.json` has it (which it does once this statusline is installed)

**I manually edited/reset the common config in the CC Switch UI and the statusline vanished again — what now?**

Just re-run `bash fix-cc-switch.sh` and restart the CC Switch app. The script is idempotent and safe to run repeatedly (it backs up the database to `cc-switch.db.bak-statusline` before each run).

## Notes

- To change color thresholds: edit the `col()` function in `quota-status.py`
- Monthly quota: shown automatically as `month X%` when Kimi's `totalQuota` field is populated

## Acknowledgments

- [ccstatusline](https://github.com/sirmalloc/ccstatusline) — the statusline renderer; cc-planbar runs as its custom-command widget
- [CC Switch](https://github.com/farion1231/cc-switch) — the provider quota endpoints and detection logic are adapted from its `coding_plan.rs` implementation
