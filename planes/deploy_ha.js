// Planes overhead: HA-side install, run in a signed-in admin HA tab (browser console or the Claude in Chrome
// JS tool). Two phases because the Flightradar24 integration (HACS) needs a core restart before its config
// flow exists. Every step is idempotent, so re-running a phase is safe.
//   await planesPhase1()   HACS download, helpers, art + template files, automations, then restart
//   await planesPhase2()   Flightradar24 entry (8 km around zone.home, 30 s), template reload, dashboard save
// Files come from the public repo pinned to the latest commit SHA (raw.githubusercontent caches 5 min per edge).

const h = document.querySelector('home-assistant').hass;
const REPO = 'ty496/ha-dashboard';
const sha = async () => (await (await fetch(`https://api.github.com/repos/${REPO}/commits/main`)).json()).sha;
const raw = (s, p) => `https://raw.githubusercontent.com/${REPO}/${s}/${p}`;
const ART = ['AAL-A319', 'AAL-A321', 'AAL-B738', 'AAY-A320', 'ACA-BCS3', 'ASA-B39M', 'ASA-B739', 'BAW-A35K',
  'DAL-A320', 'DAL-A321', 'DAL-B739', 'DAL-BCS3', 'FFT-A20N', 'FFT-A21N', 'SCX-B738', 'SWA-B737', 'SWA-B738',
  'SWA-B38M', 'UAL-A319', 'UAL-A320', 'UAL-A21N', 'UAL-B38M', 'UAL-B39M', 'UAL-B738', 'UAL-B739', 'UAL-B752',
  'UAL-B772', 'UAL-B789', 'UAX-CRJ2', 'UAX-CRJ7', 'UAX-E75L', 'GEN-C172', 'GEN-C56X', 'GEN-CL35', 'GEN-GLEX',
  'GEN-HELI', 'GEN-NARROW', 'GEN-P28A', 'GEN-PA44', 'GEN-PC12', 'GEN-REGIONAL', 'GEN-SR22', 'GEN-WIDE'];

async function planesPhase1() {
  const log = [];
  const s = await sha();
  log.push('repo at ' + s.slice(0, 7));

  // 1. Flightradar24 custom integration from HACS (downloads only; HA picks it up after the restart below).
  const repos = await h.callWS({ type: 'hacs/repositories/list' });
  const fr = repos.find(r => (r.full_name || '').toLowerCase() === 'alexandrerohin/home-assistant-flightradar24');
  if (!fr) throw new Error('Flightradar24 not in the HACS list');
  if (!fr.installed) { await h.callWS({ type: 'hacs/repository/download', repository: String(fr.id) }); log.push('HACS: downloaded Flightradar24'); }
  else log.push('HACS: Flightradar24 already installed');

  // 2. Helpers (entity ids follow from the names).
  const have = new Set(Object.keys(h.states));
  if (!have.has('input_boolean.plane_takeover'))
    await h.callWS({ type: 'input_boolean/create', name: 'Plane takeover', icon: 'mdi:airplane' });
  if (!have.has('input_text.plane_takeover_id'))
    await h.callWS({ type: 'input_text/create', name: 'Plane takeover id', max: 64, icon: 'mdi:airplane' });
  if (!have.has('counter.planes_today'))
    await h.callWS({ type: 'counter/create', name: 'Planes today', icon: 'mdi:airplane', initial: 0, step: 1, restore: true });
  log.push('helpers ok');

  // 3. Files: the art into /config/www/planes, the macros into /config/custom_templates (Downloader, download_dir ".").
  for (const k of ART)
    await h.callService('downloader', 'download_file', { url: raw(s, `www/planes/${k}.webp`), subdir: 'www/planes', filename: `${k}.webp`, overwrite: true });
  await h.callService('downloader', 'download_file', { url: raw(s, 'custom_templates/planes.jinja'), subdir: 'custom_templates', filename: 'planes.jinja', overwrite: true });
  log.push(`downloads queued: ${ART.length} images + planes.jinja`);

  // 4. Automations (same ids as the JSON files; POST replaces).
  for (const id of ['planes_overhead_takeover', 'planes_overhead_count']) {
    const cfg = await (await fetch(raw(s, `automations/${id}.json`))).json();
    await h.callApi('POST', `config/automation/config/${id}`, cfg);
  }
  log.push('automations saved');
  return log;
}

async function planesRestart() {
  await h.callService('homeassistant', 'restart', {});
  return 'restarting; wait about a minute, reload the tab, then run planesPhase2()';
}

async function planesPhase2() {
  const log = [];
  const s = await sha();

  // 5. Flightradar24 config entry: 8 km (5 mi) around home, poll every 30 s (the README asks for 20-60 s).
  const entries = await h.callWS({ type: 'config_entries/get', domain: 'flightradar24' });
  if (!entries.length) {
    const home = h.states['zone.home'].attributes;
    const flow = await h.callApi('POST', 'config/config_entries/flow', { handler: 'flightradar24', show_advanced_options: false });
    const done = await h.callApi('POST', `config/config_entries/flow/${flow.flow_id}`,
      { radius: 8000, latitude: home.latitude, longitude: home.longitude, scan_interval: 30 });
    log.push('Flightradar24 entry: ' + done.type);
  } else log.push('Flightradar24 entry already there');

  // 6. Macros and dashboard.
  await h.callService('homeassistant', 'reload_custom_templates', {});
  const show = await (await fetch(raw(s, 'show.min.json'))).json();
  await h.callWS({ type: 'lovelace/config/save', url_path: 'dashboard-show', config: show });
  log.push('dashboard saved from ' + s.slice(0, 7));
  return log;
}

// Preview the poster without waiting for a plane: point the takeover at the closest flight for 20 s.
async function planesTestTakeover() {
  const fl = (h.states['sensor.flightradar24_current_in_area'] || {}).attributes?.flights || [];
  if (!fl.length) return 'no flights in the area right now';
  await h.callService('input_text', 'set_value', { entity_id: 'input_text.plane_takeover_id', value: fl[0].id });
  await h.callService('input_boolean', 'turn_on', { entity_id: 'input_boolean.plane_takeover' });
  setTimeout(() => h.callService('input_boolean', 'turn_off', { entity_id: 'input_boolean.plane_takeover' }), 20000);
  return 'takeover on for 20 s: ' + (fl[0].callsign || fl[0].id);
}
