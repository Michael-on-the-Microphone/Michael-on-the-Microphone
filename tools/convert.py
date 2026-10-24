import csv, json, sys
src, dst = sys.argv[1], sys.argv[2]
rows = []
with open(src, newline='', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if not r['date']:
            continue
        status = r['status']
        if status == 'attended':
            s = 'went'
        elif status.startswith('past'):
            s = 'went'
        else:
            s = 'upcoming'
        artists = [a.strip() for a in r['artists'].split(',') if a.strip()] if r['artists'] else []
        venue = r['venue'].strip()
        city = 'Los Angeles'
        if 'Seattle' in venue:
            city = 'Seattle'
            venue = 'Seattle'
        venue = venue.replace(', Los Angeles', '')
        if venue == 'Shrine Expo Hall':
            venue = 'Shrine Auditorium and Expo Hall'
        rows.append({
            'date': r['date'],
            'end': r['end_date'] or None,
            'event': r['event'].strip(),
            'artists': artists,
            'venue': venue or None,
            'city': city,
            'status': s,
            'unconfirmed': status == 'past_attendance_unconfirmed' or 'not_independently_verified' in status,
        })
rows.sort(key=lambda x: x['date'])
out = "// Shared show data — generated from concert_history_2025_2026.csv\n"
out += "window.SHOWS = " + json.dumps(rows, indent=2, ensure_ascii=False) + ";\n"
out += "window.TODAY = '2026-10-24';\n"
open(dst, 'w', encoding='utf-8').write(out)
print(len(rows), 'shows')
