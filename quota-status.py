#!/usr/bin/env python3
# Statusline segment: colored Ctx% (live from stdin JSON) + coding-plan quota
# (cached 5min, provider auto-detected from ANTHROPIC_BASE_URL).
# Colors: green <60%, yellow 60-84%, red >=85%.
# ponytail: stale-cache fallback on network error; unknown providers show Ctx only.
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

TTL = 300
CACHE = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'claude-quota-cache')


def col(p):
    return '31' if p >= 85 else '33' if p >= 60 else '32'


def seg(name, p, reset_dt=None):
    r = ''
    if reset_dt:
        dt = reset_dt.astimezone()
        now = datetime.now(timezone.utc).astimezone()
        f = '%H:%M' if dt.date() == now.date() else '%m/%d %H:%M'
        r = f' (rst {dt.strftime(f)})'
    return f'\033[{col(p)}m{name} {p:.0f}%{r}\033[0m'


def load_cfg():
    env = json.load(open(os.path.expanduser('~/.claude/settings.json')))['env']
    return env.get('ANTHROPIC_BASE_URL', ''), env.get('ANTHROPIC_AUTH_TOKEN', '')


def get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=3) as r:
        return json.load(r)


def parse_iso(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')) if isinstance(s, str) else None


def kimi(base, key):
    d = get_json('https://api.kimi.com/coding/v1/usages',
                 {'Authorization': f'Bearer {key}', 'Accept': 'application/json'})
    parts = []
    for l in d.get('limits', []):
        det = l.get('detail', {})
        lim = float(det.get('limit', 1)) or 1
        parts.append(seg('5h', float(det.get('used', 0)) / lim * 100, parse_iso(det.get('resetTime'))))
        break
    u = d.get('usage')
    if u:
        lim = float(u.get('limit', 1)) or 1
        parts.append(seg('week', float(u.get('used', 0)) / lim * 100, parse_iso(u.get('resetTime'))))
    t = d.get('totalQuota') or {}
    if t.get('limit'):
        lim = float(t.get('limit', 1)) or 1
        parts.append(seg('month', float(t.get('used', 0)) / lim * 100, parse_iso(t.get('resetTime'))))
    return 'Kimi', parts


def zhipu(base, key):
    host = 'https://open.bigmodel.cn' if 'bigmodel.cn' in base else 'https://api.z.ai'
    d = get_json(f'{host}/api/monitor/usage/quota/limit',
                 {'Authorization': key, 'Accept-Language': 'en-US,en'})
    limits = [l for l in (d.get('data') or {}).get('limits', [])
              if str(l.get('type', '')).upper() == 'TOKENS_LIMIT']
    five = week = None
    other = []
    for l in limits:
        p = float(l.get('percentage', 0))
        rt = l.get('nextResetTime')
        dt = datetime.fromtimestamp(rt / 1000, timezone.utc) if isinstance(rt, (int, float)) and rt > 0 else None
        e = (p, dt)
        unit = l.get('unit')
        if unit == 3 and five is None:
            five = e
        elif unit == 6 and week is None:
            week = e
        else:
            other.append(e)
    other.sort(key=lambda e: (e[1] is not None, e[1] or datetime.min.replace(tzinfo=timezone.utc)))
    for e in other:
        if five is None:
            five = e
        elif week is None:
            week = e
    parts = []
    if five:
        parts.append(seg('5h', *five))
    if week:
        parts.append(seg('week', *week))
    return 'GLM', parts


PROVIDERS = [('api.kimi.com/coding', kimi), ('bigmodel.cn', zhipu), ('api.z.ai', zhipu)]


def provider_tag(base):
    return next((m for m, _ in PROVIDERS if m in base.lower()), 'none')


def fetch_quota():
    base, key = load_cfg()
    if not key:
        return None
    low = base.lower()
    for marker, fn in PROVIDERS:
        if marker in low:
            name, parts = fn(base, key)
            return name + ' ' + ' \033[90m·\033[0m '.join(parts) if parts else None
    return None


def quota():
    try:
        base, _ = load_cfg()
    except Exception:
        return None
    tag = provider_tag(base)
    raw = None
    try:
        raw = open(CACHE).read()
        ctag, ts, text = raw.split('\n', 2)
        if ctag == tag and time.time() - float(ts) < TTL:
            return text.rstrip('\n')
    except Exception:
        pass
    try:
        text = fetch_quota()
    except Exception:
        text = None
    if text:
        with open(CACHE, 'w') as f:
            f.write(f'{tag}\n{time.time()}\n{text}')
        return text
    if raw:
        try:
            ctag, _, text = raw.split('\n', 2)
            return text.rstrip('\n') if ctag == tag else None
        except Exception:
            pass
    return None


def main():
    d = json.load(sys.stdin)
    cw = d.get('context_window') or {}
    p = cw.get('used_percentage')
    if p is None:
        tot = (cw.get('total_input_tokens') or 0) + (cw.get('total_output_tokens') or 0)
        size = cw.get('context_window_size') or 0
        p = tot / size * 100 if size else None
    parts = []
    if p is not None:
        parts.append(f'\033[{col(p)}mCtx {p:.1f}%\033[0m')
    q = quota()
    if q:
        parts.append(q)
    print(' \033[90m|\033[0m '.join(parts), end='')


main()
