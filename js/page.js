/* Bus deserts. Every bus stop in England's Bus Open Data Service timetables on a plain MapLibre base map (OpenFreeMap
 * Positron), coloured by weekday departures, last weekday bus or Sunday service, with Wikidata villages and towns flagged by
 * the service within 800 m, and a time-of-day slider. Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => Number(n).toLocaleString('en-GB');
  const hm = m => (m < 0 ? 'none' : String(Math.floor(m / 60) % 24).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0') + (m >= 1440 ? ' (after midnight)' : ''));
  const WK = [[0, '#B9B4AA', 'none on the Tuesday'], [1, '#C8644A', '1 to 3'], [4, '#E8B04A', '4 to 11'], [12, '#9DBBD6', '12 to 47'], [48, '#4F80B0', '48 to 199'], [200, '#1F3F66', '200 or more']];
  const LAST = [[-1, '#B9B4AA', 'no weekday bus'], [0, '#7A1F12', 'before 18:00'], [1080, '#C8644A', '18:00 to 18:59'], [1140, '#E8B04A', '19:00 to 20:59'], [1260, '#9DBBD6', '21:00 to 22:59'], [1380, '#1F3F66', '23:00 or later']];
  const SUN = [[0, '#7A1F12', 'no Sunday bus'], [1, '#E8B04A', '1 to 11 on Sunday'], [12, '#4F80B0', '12 to 99'], [100, '#1F3F66', '100 or more']];
  const VCAT = ['#7A1F12', '#C8644A', '#E8B04A', '#9DBBD6', '#1F3F66'];
  const VLAB = ['no stop with a weekday bus within 800 m', '1 to 3 weekday departures', '4 to 11', '12 to 47', '48 or more'];
  let map = null, mode = 'wk', hour = 12, names = null, ST = null, PL = null;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => { ct.classList.toggle('folded', f); document.getElementById('ctToggle').setAttribute('aria-expanded', !f); };
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  const step = (prop, T) => { const e = ['step', ['get', prop], T[0][1]]; T.slice(1).forEach(t => e.push(t[0], t[1])); return e; };
  function colorExpr() {
    const base = mode === 'last' ? step('l', LAST) : mode === 'sun' ? step('s', SUN) : step('w', WK);
    if (hour <= 12) return base;
    return ['case', ['>=', ['get', 'l'], hour * 60], base, '#D6D1C6'];
  }
  function radius() {
    const big = hour > 12 ? ['case', ['>=', ['get', 'l'], hour * 60], 1, 0.55] : 1;
    const m = v => (big === 1 ? v : ['*', big, v]);
    return ['interpolate', ['linear'], ['zoom'], 5, m(['case', ['>=', ['get', 'w'], 48], 1.6, 1.2]), 8, m(['case', ['>=', ['get', 'w'], 48], 2.6, 2.0]), 11, m(4), 15, m(7)];
  }
  function key() {
    const T = mode === 'last' ? LAST : mode === 'sun' ? SUN : WK;
    document.getElementById('keyTitle').textContent = mode === 'last' ? 'Last weekday bus' : mode === 'sun' ? 'Sunday departures' : 'Weekday departures';
    document.getElementById('keyRows').innerHTML = T.map(t => `<div class="row"><span class="dot" style="background:${t[1]}"></span>${esc(t[2])}</div>`).join('') +
      (hour > 12 ? `<div class="row"><span class="dot" style="background:#D6D1C6"></span>no bus left after ${hm(hour * 60)}</div>` : '');
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
  }
  function refresh() {
    if (!map || !map.getLayer('stops')) return;
    map.setPaintProperty('stops', 'circle-color', colorExpr()); map.setPaintProperty('stops', 'circle-radius', radius()); key();
  }
  function stopPopup(i, ll) {
    const nm = names ? names[i] : 'Bus stop';
    let h = `<b class="t">${esc(nm || 'Bus stop')}</b><table>`;
    h += `<tr><td>Tuesday</td><td><b>${fmt(ST.wk[i])}</b> departures</td></tr>`;
    if (ST.wk[i] > 0) h += `<tr><td>First, last</td><td>${hm(ST.first[i])}, ${hm(ST.last[i])}</td></tr><tr><td>From 19:00</td><td>${fmt(ST.e19[i])}</td></tr>`;
    h += `<tr><td>Saturday</td><td>${fmt(ST.sat[i])}</td></tr><tr><td>Sunday</td><td>${fmt(ST.sun[i])}</td></tr></table>`;
    h += '<p class="nt">Departures of all routes calling here on one Tuesday, Saturday and Sunday in 2026. Source: Bus Open Data Service, Department for Transport (OGL v3.0).</p>';
    new maplibregl.Popup({ maxWidth: '320px' }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function placePopup(p, ll) {
    const cls = ['', 'hamlet', 'village', 'town', 'city'][p[3]];
    let h = `<b class="t">${esc(p[0])}</b><p class="nt" style="margin-top:0">${cls} · Wikidata <a href="https://www.wikidata.org/wiki/${esc(p[11])}" target="_blank" rel="noopener">${esc(p[11])}</a></p><table>`;
    h += `<tr><td>Nearest weekday bus</td><td><b>${p[4] >= 1000 ? (p[4] / 1000).toFixed(1) + ' km' : p[4] + ' m'}</b></td></tr>`;
    h += `<tr><td>Busiest stop within 800 m</td><td><b>${fmt(p[5])}</b> Tuesday departures</td></tr>`;
    if (p[5] > 0) h += `<tr><td>Last bus</td><td>${hm(p[6])}</td></tr>`;
    h += `<tr><td>Bus from 19:00</td><td>${p[7] ? 'yes' : 'no'}</td></tr><tr><td>Saturday bus</td><td>${p[8] ? 'yes' : 'no'}</td></tr><tr><td>Sunday bus</td><td>${p[9] ? 'yes' : 'no'}</td></tr></table>`;
    h += `<p class="nt"><span class="dot" style="display:inline-block;width:9px;height:9px;background:${VCAT[p[10]]}"></span> ${esc(VLAB[p[10]])}. Straight-line distance from the Wikidata point; stops within 800 m (about a ten minute walk).</p>`;
    new maplibregl.Popup({ maxWidth: '330px' }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function vfilter() {
    const f = ['all'];
    if (!document.getElementById('lyH').checked) f.push(['>=', ['get', 'c'], 2]);
    if (document.getElementById('lyD').checked) f.push(['<=', ['get', 'k'], 1]);
    map.setFilter('places', f); map.setFilter('places-lab', f);
  }
  function setup(st, pl, eng) {
    ST = st; PL = pl;
    const n = st.wk.length, feats = new Array(n);
    for (let i = 0; i < n; i++) feats[i] = { type: 'Feature', id: i, geometry: { type: 'Point', coordinates: [st.lon[i] / 1e4, st.lat[i] / 1e4] }, properties: { w: st.wk[i], l: st.last[i], s: st.sun[i] } };
    map.addSource('st', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, buffer: 32, tolerance: 0.6 });
    map.addSource('pl', { type: 'geojson', data: { type: 'FeatureCollection', features: pl.map((p, i) => ({ type: 'Feature', id: i, geometry: { type: 'Point', coordinates: [p[1], p[2]] }, properties: { n: p[0], c: p[3], k: p[10] } })) } });
    map.addSource('eng', { type: 'geojson', data: eng });
    const lbl = map.getStyle().layers.find(l => l.type === 'symbol');
    map.addLayer({ id: 'eng', type: 'line', source: 'eng', paint: { 'line-color': '#7A6A52', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 1.2, 10, 2.2], 'line-dasharray': [3, 2], 'line-opacity': 0.75 } }, lbl && lbl.id);
    map.addLayer({ id: 'stops', type: 'circle', source: 'st', paint: { 'circle-color': colorExpr(), 'circle-radius': radius(), 'circle-stroke-color': '#fff', 'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 7, 0, 10, 0.8] } });
    // squares for places: a symbol with a drawn square icon
    // one square icon per service class (white border for contrast)
    VCAT.forEach((c, k) => { const q = document.createElement('canvas'); q.width = q.height = 20; const g = q.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, 20, 20); g.fillStyle = c; g.fillRect(3, 3, 14, 14); map.addImage('sq' + k, { width: 20, height: 20, data: g.getImageData(0, 0, 20, 20).data }); });
    map.addLayer({ id: 'places', type: 'symbol', source: 'pl', filter: ['>=', ['get', 'c'], 2],
      layout: { 'icon-image': ['concat', 'sq', ['to-string', ['get', 'k']]], 'icon-size': ['interpolate', ['linear'], ['zoom'], 5, ['case', ['<=', ['get', 'k'], 0], 0.12, 0.09], 8, ['case', ['<=', ['get', 'k'], 0], 0.3, 0.22], 11, 0.5, 14, 0.75], 'icon-allow-overlap': true, 'symbol-sort-key': ['-', 5, ['get', 'k']] } });
    map.addLayer({ id: 'places-lab', type: 'symbol', source: 'pl', minzoom: 10, filter: ['>=', ['get', 'c'], 2],
      layout: { 'text-field': ['get', 'n'], 'text-size': 12, 'text-offset': [0, 1.1], 'text-anchor': 'top', 'text-font': ['Noto Sans Regular'] }, paint: { 'text-color': '#2B2119', 'text-halo-color': '#fff', 'text-halo-width': 1.4 } });
    map.on('click', e => {
      const f = map.queryRenderedFeatures([[e.point.x - 6, e.point.y - 6], [e.point.x + 6, e.point.y + 6]], { layers: ['places', 'stops'].filter(l => map.getLayoutProperty(l, 'visibility') !== 'none') });
      if (!f.length) return;
      const p = f.find(x => x.layer.id === 'places');
      if (p) placePopup(PL[p.id], p.geometry.coordinates); else stopPopup(f[0].id, f[0].geometry.coordinates);
    });
    ['stops', 'places'].forEach(l => { map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const tog = (box, ids) => document.getElementById(box).addEventListener('change', e => ids.forEach(i => map.setLayoutProperty(i, 'visibility', e.target.checked ? 'visible' : 'none')));
    tog('lyS', ['stops']); tog('lyV', ['places', 'places-lab']); tog('lyE', ['eng']);
    tog('lyL', map.getStyle().layers.filter(l => l.type === 'symbol' && !['places', 'places-lab'].includes(l.id)).map(l => l.id));
    ['lyD', 'lyH'].forEach(b => document.getElementById(b).addEventListener('change', vfilter));
    // search
    const idx = pl.map((p, i) => ({ k: norm(p[0]), i }));
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let hits = [], cur = -1;
    const CL = ['', 'hamlet', 'village', 'town', 'city'];
    function go(h) {
      const p = pl[h.i]; sug.style.display = 'none'; q.value = p[0];
      if (p[3] === 1 && !document.getElementById('lyH').checked) { document.getElementById('lyH').checked = true; vfilter(); }
      map.flyTo({ center: [p[1], p[2]], zoom: 13 }); map.once('moveend', () => placePopup(p, [p[1], p[2]]));
    }
    q.addEventListener('input', () => {
      const v = norm(q.value.trim()); cur = -1;
      if (v.length < 2) { sug.style.display = 'none'; return; }
      hits = idx.filter(x => x.k.includes(v)).sort((a, b) => (b.k.startsWith(v) - a.k.startsWith(v)) || (pl[b.i][3] - pl[a.i][3]) || a.k.length - b.k.length).slice(0, 8);
      sug.innerHTML = hits.map((h, i) => `<li role="option" data-i="${i}">${esc(pl[h.i][0])} <span>${CL[pl[h.i][3]]}</span></li>`).join('') || '<li>No match</li>';
      sug.style.display = 'block';
    });
    sug.addEventListener('click', e => { const li = e.target.closest('li[data-i]'); if (li) go(hits[+li.dataset.i]); });
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); cur = Math.max(0, Math.min(hits.length - 1, cur + (e.key === 'ArrowDown' ? 1 : -1))); sug.querySelectorAll('li').forEach((l, i) => l.setAttribute('aria-selected', i === cur)); }
      if (e.key === 'Enter' && hits.length) go(hits[Math.max(cur, 0)]);
      if (e.key === 'Escape') sug.style.display = 'none';
    });
    document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; refresh(); }));
    // time slider
    const hr = document.getElementById('hr'), hrl = document.getElementById('hrl'), play = document.getElementById('play');
    const setH = v => {
      hour = +v; hr.value = v; hrl.textContent = hour <= 12 ? 'All day' : 'After ' + hm(Math.round(hour * 60));
      // while the clock runs, show the stops only, so the evening shutdown is visible; villages come back at 'All day'
      const vis = hour <= 12 && document.getElementById('lyV').checked ? 'visible' : 'none';
      ['places', 'places-lab'].forEach(l => map.setLayoutProperty(l, 'visibility', vis)); refresh();
    };
    hr.addEventListener('input', () => setH(hr.value));
    let timer = null;
    play.addEventListener('click', () => {
      if (timer) { clearInterval(timer); timer = null; play.textContent = '▶ Play'; return; }
      play.textContent = '❚❚ Pause'; let v = hour >= 25 ? 12 : hour;
      timer = setInterval(() => { v += 0.25; setH(v); if (v >= 25) { clearInterval(timer); timer = null; play.textContent = '▶ Play'; } }, 220);
    });
    window.__setHour = setH;
    key();
    fetch('data/site_names.json').then(r => r.json()).then(x => { names = x; }).catch(() => {});
  }
  const lb = document.getElementById('lyrBtn'), lp = document.getElementById('lp');
  lb.addEventListener('click', () => { const o = !lp.classList.contains('open'); lp.classList.toggle('open', o); lb.setAttribute('aria-expanded', o); });
  map = new maplibregl.Map({ container: 'map', style: STYLE, bounds: [[-5.8, 49.9], [1.8, 55.85]], fitBoundsOptions: { padding: small ? { top: 110, bottom: 250, left: 8, right: 8 } : 30 }, attributionControl: { compact: true }, minZoom: 4.5, maxZoom: 16 });
  window.__map = map;
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
  const data = Promise.all(['data/site_stops.json', 'data/site_places.json', 'data/england.geojson'].map(u => fetch(u).then(r => r.json())));
  map.on('load', () => data.then(([s, p, e]) => { document.getElementById('nojs').style.display = 'none'; setup(s, p, e); })
    .catch(() => { document.getElementById('nojs').textContent = 'The map data could not be loaded.'; }));
})();
