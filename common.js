// Shared helpers + the little design switcher. Every design loads shows.js then this.
window.LE = (() => {
  const SHOWS = window.SHOWS;
  const TODAY = window.TODAY;
  const DESIGN_COUNT = 14;

  const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const MON = MONTHS.map(m => m.slice(0, 3));
  const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

  const d = s => new Date(s + 'T12:00:00');
  const year = s => +s.slice(0, 4);
  const month = s => +s.slice(5, 7) - 1;
  const day = s => +s.slice(8, 10);
  const weekday = s => DAYS[d(s).getDay()];

  // "Sep 27, 2026" / "27 Sep" / "September 27" etc.
  const fmt = (s, style = 'med') => {
    const y = year(s), m = month(s), dd = day(s);
    switch (style) {
      case 'short': return `${MON[m]} ${dd}`;
      case 'num': return `${String(m + 1).padStart(2, '0')}.${String(dd).padStart(2, '0')}.${String(y).slice(2)}`;
      case 'iso': return s;
      case 'long': return `${weekday(s)}, ${MONTHS[m]} ${dd}, ${y}`;
      case 'dayfirst': return `${dd} ${MON[m]} ${y}`;
      case 'month': return `${MONTHS[m]} ${y}`;
      default: return `${MON[m]} ${dd}, ${y}`;
    }
  };

  // Split "Artist: Tour name" style events into a name + a quieter subtitle.
  const split = show => {
    const e = show.event;
    let name = e, sub = '';
    let m;
    if ((m = e.match(/^(.*?):\s+(.*)$/))) { name = m[1]; sub = m[2]; }
    else if ((m = e.match(/^(.*?)\s+—\s+(.*)$/))) { name = m[1]; sub = m[2]; }
    else if ((m = e.match(/^(.*?)\s+\((.*)\)$/))) { name = m[1]; sub = m[2]; }
    else if ((m = e.match(/^(.*?)\s+presents\s+(.*)$/i))) { name = m[1]; sub = m[2]; }
    else if ((m = e.match(/^(.*?)\s+(with\s+.*)$/))) { name = m[1]; sub = m[2]; }
    else if ((m = e.match(/^(.*?)\s+(at\s+.*)$/))) { name = m[1]; sub = ''; }
    name = name.replace(/\s+presents$/i, '');
    return { name, sub };
  };

  const VENUE_SHORT = {
    'Shrine Auditorium and Expo Hall': 'The Shrine',
    'Los Angeles State Historic Park': 'LA State Historic Park',
    'LA Memorial Coliseum': 'The Coliseum',
    'McCarthy Quad, USC': 'McCarthy Quad',
    'Reframe Studios Outdoors': 'Reframe Studios',
    'Hollywood Palladium': 'The Palladium',
  };
  const venue = show => show.venue || 'Venue TBA';
  const venueShort = show => VENUE_SHORT[show.venue] || venue(show);

  const isPast = s => s.date < TODAY;
  const isToday = s => s.date === TODAY;
  const past = SHOWS.filter(isPast);
  const future = SHOWS.filter(s => s.date >= TODAY);

  const byVenue = () => {
    const map = new Map();
    SHOWS.forEach(s => {
      const v = venue(s);
      if (!map.has(v)) map.set(v, []);
      map.get(v).push(s);
    });
    return [...map.entries()].sort((a, b) => b[1].length - a[1].length || a[1][0].date.localeCompare(b[1][0].date));
  };

  const artists = () => {
    const set = new Set();
    SHOWS.forEach(s => s.artists.forEach(a => set.add(a)));
    return [...set];
  };

  // Deterministic small hash for per-show variation.
  const hash = str => { let h = 2166136261; for (const c of str) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); } return (h >>> 0); };

  const el = (tag, attrs = {}, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') n.className = v;
      else if (k === 'html') n.innerHTML = v;
      else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v);
    }
    kids.flat().forEach(k => { if (k == null) return; n.append(k.nodeType ? k : document.createTextNode(k)); });
    return n;
  };

  // Design switcher: reads the design number from the URL (/7 or /7/).
  const nav = () => {
    const m = location.pathname.match(/\/(\d+)\/?(index\.html)?$/);
    if (!m) return;
    const n = +m[1];
    const prev = n > 1 ? n - 1 : DESIGN_COUNT;
    const next = n < DESIGN_COUNT ? n + 1 : 1;
    const theme = document.documentElement.dataset.nav || 'light';
    const style = document.createElement('style');
    style.textContent = `
      .le-nav{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:9999;display:flex;align-items:center;gap:2px;
        font:500 12px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.04em;border-radius:999px;padding:4px;
        backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);box-shadow:0 2px 14px rgba(0,0,0,.18);user-select:none}
      .le-nav a{display:inline-flex;align-items:center;justify-content:center;height:28px;min-width:28px;padding:0 10px;border-radius:999px;text-decoration:none;color:inherit;opacity:.8;transition:opacity .15s,background .15s}
      .le-nav a:hover{opacity:1}
      .le-nav .cur{opacity:1;font-weight:600;padding:0 6px}
      .le-nav[data-theme=light]{background:rgba(255,255,255,.75);color:#111;border:1px solid rgba(0,0,0,.08)}
      .le-nav[data-theme=light] a:hover{background:rgba(0,0,0,.06)}
      .le-nav[data-theme=dark]{background:rgba(20,20,20,.7);color:#f2f2f2;border:1px solid rgba(255,255,255,.12)}
      .le-nav[data-theme=dark] a:hover{background:rgba(255,255,255,.1)}
      @media print{.le-nav{display:none}}`;
    document.head.append(style);
    const bar = el('div', { class: 'le-nav', 'data-theme': theme },
      el('a', { href: '../', title: 'All designs' }, 'all'),
      el('a', { href: `../${prev}/`, title: 'Previous design (←)' }, '←'),
      el('span', { class: 'cur' }, `${String(n).padStart(2, '0')} / ${DESIGN_COUNT}`),
      el('a', { href: `../${next}/`, title: 'Next design (→)' }, '→'));
    document.body.append(bar);
    document.addEventListener('keydown', e => {
      if (e.target.matches('input,textarea')) return;
      if (e.key === 'ArrowLeft') location.href = `../${prev}/`;
      if (e.key === 'ArrowRight') location.href = `../${next}/`;
    });
  };

  // Enriched research data (shows-enriched.js), optional. Everything degrades to empty when it is not loaded.
  const RICH = new Map((window.SHOWS_ENRICHED || []).map(r => [r.date + '|' + r.event, r]));
  const rich = s => RICH.get(s.date + '|' + s.event) || null;
  const lineup = s => (rich(s) && rich(s).lineup) || [];
  const headlinerName = s => (rich(s) && rich(s).headliner) || split(s).name;
  // Everyone on the bill except the headliner, in listed order.
  const support = (s, max = 3) => {
    const hl = headlinerName(s).toLowerCase();
    const bad = /\(|\b(tba|tbd|unknown|not published|unconfirmed)\b/i;
    const names = lineup(s).filter(a => a.name && a.role !== 'headliner' && a.name.toLowerCase() !== hl && !bad.test(a.name) && a.name.length <= 40).map(a => a.name);
    return max ? names.slice(0, max) : names;
  };
  const supportText = (s, max = 2) => {
    const all = support(s, 0); if (!all.length) return '';
    const shown = all.slice(0, max), rest = all.length - shown.length;
    return 'with ' + shown.join(', ') + (rest > 0 ? ` + ${rest} more` : '');
  };
  const setlist = s => {
    const sl = rich(s) && rich(s).setlist;
    if (!sl) return null;
    const songs = (sl.songs || []).map(x => x.title).filter(Boolean), encore = (sl.encore || []).map(x => x.title).filter(Boolean);
    if (!songs.length && !encore.length) return null;
    return { songs, encore, exact: !!sl.is_exact_date, url: sl.source_url || null, note: sl.note || null, total: songs.length + encore.length };
  };
  const venueInfo = s => (rich(s) && rich(s).venue) || null;
  // First plausible number in the capacity string; the primary figure comes first in strings like '70,240 (expandable to 100,000)' or 'permit for Night 2 shows 12,000'.
  const capacityNum = s => { const v = venueInfo(s); const nums = ((v && v.capacity && String(v.capacity).match(/\d[\d,]*/g)) || []).map(x => parseInt(x.replace(/,/g, ''), 10)).filter(x => x >= 100 && x < 200000); return nums.length ? nums[0] : null; };
  const cleanTime = t => {
    if (!t) return null;
    let x = String(t).replace(/\([^)]*\)/g, '').split(/[;,]| both | per /)[0];
    x = x.replace(/\b(doors?|show|starts?|at)\b:?/ig, '').replace(/:00\b/g, '').replace(/\s*([AP])\.?M\b/i, ' $1M').replace(/\s+/g, ' ').trim();
    return /\d/.test(x) ? x : null;
  };
  const schedule = s => (rich(s) && rich(s).schedule) || {};
  const doors = s => cleanTime(schedule(s).doors);
  const showStart = s => cleanTime(schedule(s).show_start);
  const ageLimit = s => { const a = schedule(s).age_restriction; const m = a && String(a).match(/(\d\d\+|all ages)/i); return m ? m[1] : null; };
  const facts = s => [...((rich(s) && rich(s).production) || []), ...((rich(s) && rich(s).facts) || [])];
  // Shortest fact that still says something, for captions.
  const blurb = (s, max = 110) => {
    const dull = /setlist\.fm|users|logged|ticket|presale|on sale|stubhub|axs|dice|\$|price|resale|boxscore|gross|verified|unverified|listing|sources?\b|\bbrief\b|portfolio owner|attendee review|fan report|promoted by|-listed|insomniac|goldenvoice|bandsintown|partiful|wikipedia/i;
    const cut = f => f.length <= max ? f : f.slice(0, max - 1).replace(/\s+\S*$/, '') + '…';
    const all = facts(s).filter(Boolean);
    const good = all.filter(f => !dull.test(f)).sort((a, b) => a.length - b.length);
    const fit = good.filter(f => f.length <= max);
    if (fit.length) return fit[Math.min(1, fit.length - 1)];
    if (good.length) return cut(good[0]);
    const rest = all.slice().sort((a, b) => a.length - b.length);
    return rest.length ? cut(rest[0]) : '';
  };
  const tourName = s => (rich(s) && rich(s).tour && rich(s).tour.name) || null;
  const tourBlurb = s => { const d = rich(s) && rich(s).tour && rich(s).tour.description; return d ? d.split(/(?<=\.)\s/)[0] : null; };
  const press = s => (rich(s) && rich(s).press) || [];

  return { SHOWS, TODAY, DESIGN_COUNT, MONTHS, MON, DAYS, d, year, month, day, weekday, fmt, split, venue, venueShort, isPast, isToday, past, future, byVenue, artists, hash, el, nav, rich, lineup, support, supportText, setlist, venueInfo, capacityNum, doors, showStart, ageLimit, facts, blurb, tourName, tourBlurb, press };
})();
