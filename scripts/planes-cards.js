// Adds the planes-overhead cards to the Show's home view (2026-10-30), idempotently:
// - "Overhead now": glass markdown card at the top of the right column, shown while any flight is in the
//   Flightradar24 area (closest flight, its drawing from /local/planes, route and altitude/speed/type chips).
// - Poster takeover: full-screen FlightPortrait-style print, shown while input_boolean.plane_takeover is on
//   (the planes_overhead_takeover automation turns it on for 20 s, at most every 15 min, 07:00-22:00).
// Lookup and caption macros live in custom_templates/planes.jinja.
const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, '..', 'show.json');
const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
const home = cfg.views.find(v => v.path === 'home');

const IMPORT = "{% from 'planes.jinja' import plane_pick, plane_art, plane_where, plane_trend, plane_flight, plane_route, plane_model, plane_alt, plane_mph %}";
const FLIGHT = id => `{% set id = plane_pick(${id}) | trim %}` +
  "{% set f = (state_attr('sensor.flightradar24_current_in_area', 'flights') or []) | selectattr('id', 'eq', id) | first if id else none %}";

const overhead = {
  type: 'markdown',
  name: 'Overhead now',
  grid_options: { columns: 'full' },
  visibility: [{ condition: 'numeric_state', entity: 'sensor.flightradar24_current_in_area', above: 0 }],
  content: [
    IMPORT, FLIGHT("''"), '{% if f %}',
    '#### ✈︎ OVERHEAD NOW <span>{{ plane_where(f) }} · {{ plane_trend(f) }}</span>',
    '',
    '<img src="{{ plane_art(f) }}">',
    '',
    '# {{ plane_flight(f) }}',
    '{{ plane_route(f) }}',
    '',
    '| {{ plane_alt(f) }} | {{ plane_mph(f) }} | {{ plane_model(f) }} |',
    '|:-:|:-:|:-:|',
    "| ft | mph | {{ f.aircraft_registration or '' }} |",
    '{% endif %}',
  ].join('\n'),
  card_mod: {
    style: {
      'ha-markdown$': [
        'ha-markdown-element { display: grid; grid-template-columns: 1fr auto; column-gap: 12px; align-items: end; }',
        'h4, img { grid-column: 1 / -1; }',
        'h4 { display: flex; justify-content: space-between; margin: 0; font-size: 15px; font-weight: 600; letter-spacing: .3px; color: var(--primary-color); }',
        'h4 span { color: var(--secondary-text-color); }',
        'img { display: block; width: 100%; margin: 10px 0 6px; filter: drop-shadow(0 10px 12px rgba(20, 30, 60, .22)); }',
        'h1 { grid-column: 1; margin: 2px 0 0; font-size: 30px; font-weight: 700; line-height: 1.1; }',
        'p { grid-column: 1; margin: 2px 0 0; font-size: 18px; color: var(--secondary-text-color); }',
        'table { grid-column: 2; grid-row: 3 / span 2; border-collapse: separate; border-spacing: 8px 0; margin: 0; }',
        'th, td { background: rgba(255, 255, 255, .55); text-align: center; border: 0; }',
        'th { padding: 6px 10px 0; border-radius: 12px 12px 0 0; font-size: 17px; font-weight: 700; }',
        'td { padding: 0 10px 6px; border-radius: 0 0 12px 12px; font-size: 13px; color: var(--secondary-text-color); }',
      ].join('\n'),
    },
  },
};

const takeover = {
  type: 'markdown',
  name: 'Plane poster takeover',
  visibility: [{ condition: 'state', entity: 'input_boolean.plane_takeover', state: 'on' }],
  content: [
    IMPORT, FLIGHT("states('input_text.plane_takeover_id')"), '{% if f %}',
    "{% set lat = state_attr('zone.home', 'latitude') | float(0) %}{% set lon = state_attr('zone.home', 'longitude') | float(0) %}",
    '##### OVERHEAD',
    '### {{ plane_where(f) }} · {{ plane_trend(f) }}',
    '',
    '<img src="{{ plane_art(f) }}">',
    '',
    "## {{ f.airline or 'Private' }} · {{ f.aircraft_model or f.aircraft_code }}",
    "{{ [f.flight_number, plane_route(f), f.aircraft_registration, plane_alt(f) ~ ' ft'] | select | join(' · ') }}",
    '',
    "###### No {{ states('counter.planes_today') }} today · {{ now().strftime('%A %-d %B %Y') }} · " +
      "{{ '%.2f' | format(lat | abs) }}° {{ 'N' if lat >= 0 else 'S' }} {{ '%.2f' | format(lon | abs) }}° {{ 'W' if lon < 0 else 'E' }} · Wheat Ridge, Colorado",
    '{% endif %}',
  ].join('\n'),
  card_mod: {
    style: {
      '.': [
        'ha-card { position: fixed !important; inset: 0 !important; z-index: 1000; margin: 0; padding: 0 !important;',
        '  border: 0 !important; border-radius: 0 !important; box-shadow: none !important;',
        '  backdrop-filter: none !important; -webkit-backdrop-filter: none !important;',
        "  background: #8d0e12 !important; color: #f3e6c8; font-family: Georgia, 'Times New Roman', serif; }",
      ].join('\n'),
      'ha-markdown$': [
        'ha-markdown-element { position: absolute; inset: 0; }',
        'h5 { position: absolute; left: 5vw; top: 6.5vh; margin: 0; font-size: 15px; font-weight: 400; letter-spacing: 5px; }',
        'h3 { position: absolute; right: 5vw; top: 6.5vh; margin: 0; font-size: 13px; font-weight: 400; letter-spacing: 3px; text-transform: uppercase; opacity: .8; }',
        'img { position: absolute; left: 5.5vw; top: 24vh; width: 89vw; filter: drop-shadow(0 18px 18px rgba(0, 0, 0, .25)); }',
        'h2 { position: absolute; left: 9.4vw; top: 73.5vh; margin: 0; font-size: 30px; font-weight: 400; }',
        'p { position: absolute; left: 9.4vw; top: 79.5vh; margin: 0; font-size: 19px; opacity: .85; }',
        "h6 { position: absolute; left: 5vw; right: 5vw; bottom: 5.5vh; margin: 0; text-align: center; font-family: 'Segoe UI', Roboto, sans-serif; font-size: 11px; font-weight: 400; letter-spacing: 2.4px; text-transform: uppercase; opacity: .7; }",
      ].join('\n'),
    },
  },
};

// Right column: after "Needs attention" (index 0). Takeover: anywhere, it is position: fixed; put it in the
// bottom-bar section with the pop-ups.
const right = home.sections[1].cards;
const bar = home.sections[2].cards;
const strip = cards => cards.filter(c => c.name !== 'Overhead now' && c.name !== 'Plane poster takeover');
home.sections[1].cards = strip(right);
home.sections[1].cards.splice(1, 0, overhead);
home.sections[2].cards = [...strip(bar), takeover];

fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n');
fs.writeFileSync(path.join(__dirname, '..', 'show.min.json'), JSON.stringify(cfg));
console.log('planes cards in place:', home.sections.map(s => s.cards.length + ' cards').join(', '));
