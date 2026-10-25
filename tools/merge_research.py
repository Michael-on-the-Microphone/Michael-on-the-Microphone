"""Merge per-show research files into shows-enriched.json / .js / .md.

Usage: python3 -I tools/merge_research.py <dir with research *.json files>
Records are keyed on (date, event) against shows.js. New research wins where it is
better: an exact-date setlist replaces a reference one, a longer lineup replaces a
shorter one, facts and sources are unioned. Shows with no prior record get one.
"""
import json, sys, glob, os

src = sys.argv[1]
shows = json.loads(open('shows.js').read().split('window.SHOWS = ', 1)[1].rsplit(';', 1)[0])
old = {(r['date'], r['event']): r for r in json.load(open('shows-enriched.json'))}

def songs_of(sl):
    return len((sl or {}).get('songs') or []) + len((sl or {}).get('encore') or [])

def convert_setlist(new):
    if not new:
        return None
    main, enc = [], []
    for i, s in enumerate(new.get('songs') or []):
        if not s.get('title'):
            continue
        row = {'n': s.get('n') or i + 1, 'title': s['title'], 'notes': s.get('notes')}
        (enc if s.get('encore') else main).append(row)
    out = {'source_url': new.get('source_url'), 'is_exact_date': bool(new.get('is_exact_date')),
           'note': new.get('note'), 'songs': main, 'encore': enc}
    if new.get('reference_date') and not new.get('is_exact_date'):
        out['reference_date'] = new['reference_date']
    return out

def union(a, b):
    seen, out = set(), []
    for x in (a or []) + (b or []):
        k = json.dumps(x, sort_keys=True) if not isinstance(x, str) else x.strip().lower()
        if k not in seen:
            seen.add(k); out.append(x)
    return out

report = []
for f in sorted(glob.glob(os.path.join(src, '*.json'))):
    n = json.load(open(f))
    key = (n['date'], n['event'])
    show = next((s for s in shows if (s['date'], s['event']) == key), None)
    if not show:
        report.append(f'UNMATCHED {os.path.basename(f)}: {key}'); continue
    r = old.get(key) or {**show, 'venue_name': show['venue'], 'venue': {'name': show['venue']}}
    before = (songs_of(r.get('setlist')), bool((r.get('setlist') or {}).get('is_exact_date')), len(r.get('lineup') or []))
    r['headliner'] = n.get('headliner') or r.get('headliner')
    # lineup: replace when the new one is at least as complete; normalise field name
    nl = [{'name': a.get('name'), 'role': a.get('role'), 'set_time': a.get('set_time'),
           'stage': a.get('stage_or_day') or a.get('stage'), 'notes': a.get('notes')} for a in (n.get('lineup') or []) if a.get('name')]
    if len(nl) >= len(r.get('lineup') or []):
        r['lineup'] = nl
    # setlist: exact beats reference, then more songs beats fewer
    ns = convert_setlist(n.get('setlist'))
    os_ = r.get('setlist') or {}
    if ns and songs_of(ns):
        better = (ns['is_exact_date'] and not os_.get('is_exact_date')) or \
                 (ns['is_exact_date'] == bool(os_.get('is_exact_date')) and songs_of(ns) >= songs_of(os_))
        if better or not songs_of(os_):
            r['setlist'] = ns
    elif not os_ and ns:
        r['setlist'] = ns
    sch = r.get('schedule') or {}
    for k, v in (n.get('schedule') or {}).items():
        if v and not sch.get(k):
            sch[k] = v
    r['schedule'] = sch
    r['facts'] = union(n.get('facts'), r.get('facts'))
    r['sources'] = union(r.get('sources'), n.get('sources'))
    r['gaps'] = n.get('gaps') or r.get('gaps')
    r['confidence'] = n.get('confidence') or r.get('confidence')
    if n.get('verification'):
        r['verification'] = n['verification']
    old[key] = r
    after = (songs_of(r.get('setlist')), bool((r.get('setlist') or {}).get('is_exact_date')), len(r.get('lineup') or []))
    v = n.get('verification') or {}
    flag = '' if (v.get('date_ok', True) and v.get('venue_ok', True)) else '  !! CHECK: ' + (v.get('notes') or '')[:160]
    report.append(f"{key[0]} {key[1][:34]:34} setlist {before[0]:>2}{'*' if before[1] else ' '} -> {after[0]:>2}{'*' if after[1] else ' '}  lineup {before[2]:>2} -> {after[2]:>2}{flag}")

order = {(s['date'], s['event']): i for i, s in enumerate(sorted(shows, key=lambda s: s['date']))}
recs = sorted(old.values(), key=lambda r: order.get((r['date'], r['event']), 999))
json.dump(recs, open('shows-enriched.json', 'w'), indent=2, ensure_ascii=False)
open('shows-enriched.js', 'w').write('// Enriched show data, merged from web research. See shows-enriched.md for a readable version.\nwindow.SHOWS_ENRICHED = '
                                     + json.dumps(recs, indent=2, ensure_ascii=False) + ';\n')

# readable markdown
md = ['# Shows, enriched', '', f'{len(recs)} shows. `*` after a count means the setlist is from that exact night.', '']
for r in recs:
    vn = r['venue']['name'] if isinstance(r.get('venue'), dict) else r.get('venue')
    md += [f"## {r['event']}", f"**{r['date']}**{' to ' + r['end'] if r.get('end') else ''} · {vn or 'Venue TBA'} · confidence {r.get('confidence') or '?'}", '']
    v = r.get('verification')
    if v and v.get('notes'):
        md += [f"**Check:** {v['notes']}", '']
    if r.get('lineup'):
        md += ['**Lineup**'] + [f"- {a['name']} ({a.get('role') or '?'})" + (f", {a['set_time']}" if a.get('set_time') else '') + (f", {a['stage']}" if a.get('stage') else '') + (f" — {a['notes']}" if a.get('notes') else '') for a in r['lineup']] + ['']
    sl = r.get('setlist') or {}
    if songs_of(sl):
        tag = 'exact night' if sl.get('is_exact_date') else f"reference{', ' + sl['reference_date'] if sl.get('reference_date') else ''}"
        md += [f"**Setlist** ({tag})" + (f" · {sl['source_url']}" if sl.get('source_url') else '')]
        if sl.get('note'): md += [f"_{sl['note']}_"]
        md += [f"{i+1}. {s['title']}" + (f" — {s['notes']}" if s.get('notes') else '') for i, s in enumerate(sl.get('songs') or [])]
        if sl.get('encore'): md += ['', 'Encore:'] + [f"- {s['title']}" + (f" — {s['notes']}" if s.get('notes') else '') for s in sl['encore']]
        md += ['']
    else:
        md += ['**Setlist:** none found', '']
    if r.get('facts'): md += ['**Facts**'] + [f'- {x}' for x in r['facts'][:6]] + ['']
    if r.get('gaps'): md += ['**Still missing:** ' + '; '.join(r['gaps'] if isinstance(r['gaps'], list) else [str(r['gaps'])]), '']
open('shows-enriched.md', 'w').write('\n'.join(md))
print('\n'.join(report)); print(f'\n{len(recs)} records written')
