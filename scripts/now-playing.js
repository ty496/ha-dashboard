// Now Playing for the Family Room Stereo on the Show's home view (2026-11-03), idempotently:
// - A compact player at the foot of the left column while the WiiM plays or is paused: a small square of
//   album art, title and artist, then a strip of controls and volume, with a Stop button beside it
//   (script.family_room_stereo_stop: stop, clear Music Assistant's queue, Pioneer off). Art and words
//   read the WiiM's own entity, so music started outside Music Assistant shows too; controls use Music
//   Assistant's player while it streams, because the WiiM's entity then has no next or previous.
// - While the WiiM plays, the dashboard background is the album art (the matt8707 community look, Tidal
//   and Spotify style): the cover, sharp, in the middle at about two-thirds of the screen's height, over a
//   heavily blurred stretch of the same art that fills the rest with its average colours. Two fixed
//   markdown cards behind the glass cards (z-index -1, the colour wash first). Ty: a blurred, screen-high
//   cover looked "like a bad screen shot of the art".
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
const MA_ON = { condition: 'state', entity: MA, state: ['playing', 'paused'] };
const MA_OFF = { condition: 'state', entity: MA, state_not: ['playing', 'paused'] };
const ART = `{{ state_attr('${E}', 'entity_picture') or '' }}`;
const FULL_SCREEN = 'position: fixed !important; z-index: -1 !important; pointer-events: none !important; border: none !important; border-radius: 0 !important; box-shadow: none !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important; max-height: none !important;';

const playerFor = (entity, visibility) => ({
  type: 'custom:mini-media-player',
  entity,
  artwork: 'default',
  info: 'scroll',
  volume_step: 5,
  hide: { power: true, source: true, name: true },
  grid_options: { columns: 9 },
  visibility,
  card_mod: { style: 'ha-card { border-radius: 24px; --mmp-unit: 36px; } .entity__artwork, .entity__icon { width: 60px !important; height: 60px !important; min-width: 60px !important; border-radius: 12px !important; background-size: cover !important; } .entity__info__media, .entity__info__media span { font-size: 18px !important; font-weight: 600 !important; color: var(--primary-text-color) !important; opacity: 1 !important; }' },
});
const stop = {
  type: 'button',
  name: 'Stop',
  icon: 'mdi:stop',
  show_name: true,
  show_icon: true,
  tap_action: { action: 'perform-action', perform_action: 'script.family_room_stereo_stop' },
  hold_action: { action: 'none' },
  grid_options: { columns: 3, rows: 'auto' },
  visibility: [{ condition: 'or', conditions: [{ condition: 'state', entity: E, state: ['playing', 'paused'] }, MA_ON] }],
  card_mod: { style: 'ha-card { border-radius: 24px; height: 100% !important; } ha-state-icon { --mdc-icon-size: 40px; }' },
};
const cards = [
  playerFor(MA, [MA_ON]),
  playerFor(E, [{ condition: 'state', entity: E, state: ['playing', 'paused'] }, MA_OFF]),
  stop,
];
const wash = {
  type: 'markdown',
  name: 'Now playing background',
  content: ' ',
  visibility: [{ condition: 'state', entity: E, state: 'playing' }],
  card_mod: { style: `ha-card { ${FULL_SCREEN} top: -300px !important; left: -300px !important; width: calc(100vw + 600px) !important; height: calc(100vh + 600px) !important; background: center / 100% 100% no-repeat url('${ART}') !important; filter: blur(140px) saturate(1.25) brightness(0.6); }` },
};
const coverArt = {
  type: 'markdown',
  name: 'Now playing cover',
  content: ' ',
  visibility: [{ condition: 'state', entity: E, state: 'playing' }],
  card_mod: { style: `ha-card { ${FULL_SCREEN} top: 18vh !important; left: calc(50vw - 32vh) !important; width: 64vh !important; height: 64vh !important; border-radius: 16px !important; box-shadow: 0 24px 64px rgba(0, 0, 0, 0.5) !important; background: center / cover no-repeat url('${ART}') !important; filter: brightness(0.6); }` },
};

// The player and its Stop button sit at the foot of the left column; anything earlier is cleared out.
const old = right.findIndex(c => c.type === 'media-control' && c.entity === E);
if (old >= 0) right.splice(old, 1);
const mine = c => (c.type === 'custom:mini-media-player' && [E, MA].includes(c.entity)) || (c.type === 'button' && c.tap_action && c.tap_action.perform_action === 'script.family_room_stereo_stop');
for (const list of [left, right]) for (let i = list.length - 1; i >= 0; i--) if (mine(list[i])) list.splice(i, 1);
left.push(...cards);

// Backdrop: colour wash first, then the cover over it. The pop-up goes.
for (let i = popups.length - 1; i >= 0; i--) if (['Now playing background', 'Now playing cover'].includes(popups[i].name) || popups[i].hash === '#now-playing') popups.splice(i, 1);
popups.push(wash, coverArt);

fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n');
fs.writeFileSync(path.join(__dirname, '..', 'show.min.json'), JSON.stringify(cfg));
const s = JSON.stringify(cfg); let x = 0x811c9dc5; for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 0x01000193) >>> 0; }
console.log('show.json', x.toString(16), s.length);
if (process.argv.includes('--print')) console.log(JSON.stringify({ cards, wash, coverArt }));
