// Now Playing on the Show's home view (2026-11-03), idempotently, for the Family Room Stereo and for
// Music Assistant's Whole House group (Kitchen Echo + HomePod; the group wins when both are on):
// - HA's own media card at the foot of the left column while the WiiM plays or is paused (the style of the
//   HomePod's card, which Ty preferred to the compact mini-media-player: it shows more), with a Stop button
//   beside it (script.family_room_stereo_stop: stop, clear Music Assistant's queue, Pioneer off). The WiiM's
//   own entity's card shows music started outside Music Assistant too; Music Assistant's player's card takes
//   over while it streams, because the WiiM's entity then has no next or previous.
// - While the WiiM plays, the dashboard background is the album art (the matt8707 community look, Tidal
//   and Spotify style): the cover, sharp, in the middle at about two-thirds of the screen's height, over a
//   heavily blurred stretch of the same art that fills the rest with its average colours. Two fixed
//   markdown cards behind the glass cards (z-index -1, the colour wash first). Ty: a blurred, screen-high
//   cover looked "like a bad screen shot of the art".
// - The Sunrise, Sunset and Moon tiles above it are one row, icon beside the words, rather than two with the
//   icon above (Ty: "a lot of open area in the tile"), to make room for the taller card.
// Ty dropped the 30 s full-screen pop-up on each new song the same day ("I like it just staying as a
// small control"); this removes it if present.
const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, '..', 'show.json');
const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
const home = cfg.views.find(v => v.path === 'home');
const left = home.sections[0].cards;
const right = home.sections[1].cards;
const popups = home.sections.find(s => s.cards.some(c => c.card_type === 'pop-up')).cards;

const E = 'media_player.family_room_family_room_wiim';
const MA = 'media_player.family_room_stereo';
const WH = 'media_player.whole_house';
const MA_ON = { condition: 'state', entity: MA, state: ['playing', 'paused'] };
const MA_OFF = { condition: 'state', entity: MA, state_not: ['playing', 'paused'] };
const WH_ON = { condition: 'state', entity: WH, state: ['playing', 'paused'] };
const WH_OFF = { condition: 'state', entity: WH, state_not: ['playing', 'paused'] };
const ART = `{{ state_attr('${WH}' if is_state('${WH}', 'playing') else '${E}', 'entity_picture') or '' }}`;
const SHOWING = { condition: 'or', conditions: [{ condition: 'state', entity: E, state: 'playing' }, { condition: 'state', entity: WH, state: 'playing' }] };
const FULL_SCREEN = 'position: fixed !important; z-index: -1 !important; pointer-events: none !important; border: none !important; border-radius: 0 !important; box-shadow: none !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important; max-height: none !important;';

const playerFor = (entity, visibility) => ({ type: 'media-control', entity, grid_options: { columns: 9 }, visibility });
const stop = {
  type: 'button',
  name: 'Stop',
  icon: 'mdi:stop',
  show_name: true,
  show_icon: true,
  tap_action: { action: 'perform-action', perform_action: 'script.family_room_stereo_stop' },
  hold_action: { action: 'none' },
  grid_options: { columns: 3, rows: 'auto' },
  visibility: [{ condition: 'or', conditions: [{ condition: 'state', entity: E, state: ['playing', 'paused'] }, MA_ON, WH_ON] }],
  card_mod: { style: 'ha-card { border-radius: 24px; height: 100% !important; } ha-state-icon { --mdc-icon-size: 40px; }' },
};
const cards = [
  playerFor(WH, [WH_ON]),
  playerFor(MA, [MA_ON, WH_OFF]),
  playerFor(E, [{ condition: 'state', entity: E, state: ['playing', 'paused'] }, MA_OFF, WH_OFF]),
  stop,
];
const wash = {
  type: 'markdown',
  name: 'Now playing background',
  content: ' ',
  visibility: [SHOWING],
  card_mod: { style: `ha-card { ${FULL_SCREEN} top: -300px !important; left: -300px !important; width: calc(100vw + 600px) !important; height: calc(100vh + 600px) !important; background: center / 100% 100% no-repeat url('${ART}') !important; filter: blur(140px) saturate(1.25) brightness(0.6); }` },
};
const coverArt = {
  type: 'markdown',
  name: 'Now playing cover',
  content: ' ',
  visibility: [SHOWING],
  card_mod: { style: `ha-card { ${FULL_SCREEN} top: 18vh !important; left: calc(50vw - 32vh) !important; width: 64vh !important; height: 64vh !important; border-radius: 16px !important; box-shadow: 0 24px 64px rgba(0, 0, 0, 0.5) !important; background: center / cover no-repeat url('${ART}') !important; filter: brightness(0.6); }` },
};

// The player and its Stop button sit at the foot of the left column; anything earlier is cleared out.
const old = right.findIndex(c => c.type === 'media-control' && c.entity === E);
if (old >= 0) right.splice(old, 1);
const mine = c => (['custom:mini-media-player', 'media-control'].includes(c.type) && [E, MA, WH].includes(c.entity)) ||(c.type === 'button' && c.tap_action && c.tap_action.perform_action === 'script.family_room_stereo_stop');
for (const list of [left, right]) for (let i = list.length - 1; i >= 0; i--) if (mine(list[i])) list.splice(i, 1);
left.push(...cards);
// The HomePod's stock media card, shown while the HomePod plays on its own (Music Assistant or AirPlay from a
// phone), sits under the player in the left column (Ty liked it there better than in the right column, under
// the calendar), and stays out of the way while the HomePod is playing as part of the Whole House group.
const isHomepodCard = c => c.type === 'media-control' && c.entity === 'media_player.family_room_family_room_homepod';
const homepod = [...left, ...right].find(isHomepodCard);
for (const list of [left, right]) for (let i = list.length - 1; i >= 0; i--) if (isHomepodCard(list[i])) list.splice(i, 1);
if (homepod) {
  homepod.visibility = [{ condition: 'state', entity: 'media_player.family_room_family_room_homepod', state: 'playing' }, WH_OFF];
  left.push(homepod);
}

// The sun and moon tiles, side by side in one row: horizontal tiles, inside a grid card because the sections
// grid gives a horizontal tile at least half the column (Moon wrapped to a second row).
const SUN_MOON = ['Sunrise', 'Sunset', 'Moon'];
const isSunMoon = c => c.type === 'tile' && SUN_MOON.includes(c.name);
const isSunMoonRow = c => c.type === 'grid' && (c.cards || []).some(isSunMoon);
let rowAt = left.findIndex(c => isSunMoon(c) || isSunMoonRow(c));
const tiles = left.flatMap(c => (isSunMoonRow(c) ? c.cards : [c])).filter(isSunMoon);
for (let i = left.length - 1; i >= 0; i--) if (isSunMoon(left[i]) || isSunMoonRow(left[i])) left.splice(i, 1);
for (const t of tiles) { t.vertical = false; delete t.grid_options; }
if (rowAt >= 0) left.splice(rowAt, 0, { type: 'grid', columns: 3, square: false, grid_options: { columns: 'full' }, cards: SUN_MOON.map(n => tiles.find(t => t.name === n)).filter(Boolean) });

// Backdrop: colour wash first, then the cover over it, each replaced where it stands (so the pop-ups after
// them, Music's included, keep their order). The pop-up goes.
for (let i = popups.length - 1; i >= 0; i--) if (popups[i].hash === '#now-playing') popups.splice(i, 1);
for (const card of [wash, coverArt]) {
  const at = popups.findIndex(c => c.name === card.name);
  if (at >= 0) popups[at] = card; else popups.push(card);
}

fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n');
fs.writeFileSync(path.join(__dirname, '..', 'show.min.json'), JSON.stringify(cfg));
const s = JSON.stringify(cfg); let x = 0x811c9dc5; for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 0x01000193) >>> 0; }
console.log('show.json', x.toString(16), s.length);
if (process.argv.includes('--print')) console.log(JSON.stringify({ cards, wash, coverArt }));
