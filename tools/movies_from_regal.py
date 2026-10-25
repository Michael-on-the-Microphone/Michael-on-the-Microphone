"""Build data/movies.js from a Regal bookings export (.xlsx).

Usage: python3 -I tools/movies_from_regal.py ~/Downloads/regal_movie_bookings_2025_2026.xlsx data/movies.js
Extra screenings not in the export go in data/movies_extra.csv (date,title,where,format,note; where defaults to Regal LA Live); same date+title is skipped.
Keep the export out of the repo: it holds booking codes and mailbox links.
Refunded bookings are skipped. Dates are the booking confirmation dates (the export has no
show dates), except Monday Mystery Movies, whose titles carry the real show date.
"""
import json, re, sys, datetime, csv, os
import openpyxl

src, dst = sys.argv[1], sys.argv[2]
ws = openpyxl.load_workbook(src, data_only=True)['All Bookings']
rows = list(ws.iter_rows(values_only=True))[1:]

FORMATS = {'IMAX': 'IMAX', '4DX': '4DX', 'RPX': 'RPX', 'PLF': 'PLF', 'ICE': 'ICE'}
out = []
for conf, title, tickets, code, refund, total, *_ in rows:
    if not conf or not title or refund == 'Refunded':
        continue
    date = conf.date()
    t = str(title).strip()
    fmt, notes = [], []
    m = re.match(r'^(IMAX|4DX|RPX|PLF|ICE):\s*(.*)$', t)
    if m:
        fmt.append(FORMATS[m.group(1)]); t = m.group(2)
    for tag in ('70mm', '3D', '4K'):
        if re.search(r'\b' + tag + r'\b', t):
            fmt.append(tag); t = re.sub(r'\s*\b' + tag + r'\b', '', t)
    m = re.search(r'\s*-\s*(Early Access.*|Fan First.*|The Finale|Horror Edition)$', t)
    if m:
        notes.append(m.group(1).replace(' Screenings', '').strip()); t = t[:m.start()]
    m = re.search(r'\s*\((Tamil|Hindi|Malayalam|Sub)\)$', t)
    if m:
        notes.append('Subtitled' if m.group(1) == 'Sub' else m.group(1)); t = t[:m.start()]
    m = re.search(r'\s*(\d{1,2}(?:th|st)) Anniversary$', t)
    if m:
        notes.append(m.group(1) + ' anniversary screening'); t = t[:m.start()]
    m = re.match(r'^Monday Mystery Movie \((\d{1,2})/(\d{1,2})\)(.*)$', t)
    if m:
        mo, dd = int(m.group(1)), int(m.group(2))
        yr = date.year + (1 if mo < date.month - 6 else 0)
        date = datetime.date(yr, mo, dd)
        t = 'Monday Mystery Movie'
        if m.group(3).strip(' -'):
            notes.append(m.group(3).strip(' -'))
    if tickets and tickets > 1:
        notes.append('with a friend' if tickets == 2 else f'with {tickets - 1} friends')
    out.append({
        'date': date.isoformat(), 'title': t.strip(), 'where': 'Regal LA Live',
        'format': ' '.join(fmt) if fmt else None, 'note': ', '.join(notes) if notes else None,
    })
extra = os.path.join(os.path.dirname(dst), 'movies_extra.csv')
if os.path.exists(extra):
    seen = {(m['date'], m['title'].lower()) for m in out}
    with open(extra, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if (r['date'], r['title'].lower()) in seen:
                continue
            out.append({'date': r['date'], 'title': r['title'], 'where': r.get('where') or 'Regal LA Live',
                        'format': r.get('format') or None, 'note': r.get('note') or None})
out.sort(key=lambda m: m['date'])
hdr = ("// Movies. Generated from the Regal bookings export by tools/movies_from_regal.py.\n"
       "// Dates are booking dates (the export has no show dates), except Monday Mystery Movies.\n"
       "// Fields: date, title, year, where, format, note, status ('seen' by default, or 'want').\n")
open(dst, 'w', encoding='utf-8').write(hdr + 'window.MOVIES = ' + json.dumps(out, indent=2, ensure_ascii=False) + ';\n')
print(len(out), 'screenings')
