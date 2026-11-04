// Now Playing on the Show's home view (2026-11-03), idempotently, for every speaker Music Assistant plays on:
// - One player at the foot of the left column for whichever speaker is playing or paused, first in this
//   order: the Whole House group, the Family Room Stereo (Music Assistant's player, then the WiiM's own for
//   music started outside it), the HomePod (Music Assistant's, then Apple's for AirPlay from a phone), the
//   Kitchen Echo. mini-media-player in its material artwork mode, laid out like HA's own media card (Ty
//   preferred that look: it shows more) but keeping a Stop button inside the card (script.music_stop: the
//   stereo and the group through script.family_room_stereo_stop, Pioneer off with the stereo; any other
//   speaker stopped and its queue cleared), the volume slider, and a tap opening the Music pop-up
//   (music-popup.js). HA's media card itself was tried the same evening: it takes no extra button, and it
//   covered no speaker alone but the HomePod (switching to the Kitchen alone left nothing on screen).
// - While any of them plays, the dashboard background is its album art (the matt8707 community look, Tidal
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
const HP = 'media_player.homepod';
const HP_APPLE = 'media_player.family_room_family_room_homepod';
const KITCHEN = 'media_player.kitchen';
// Highest first: a speaker's player shows only while none above it is playing or paused (the group's
// members and the WiiM under Music Assistant play too, so the group's or Music Assistant's player wins).
const PLAYERS = [WH, MA, E, HP, HP_APPLE, KITCHEN];
const on = entity => ({ condition: 'state', entity, state: ['playing', 'paused'] });
const off = entity => ({ condition: 'state', entity, state_not: ['playing', 'paused'] });
// The art behind the cards: the first of them playing that has a picture (the WiiM's own before Music
// Assistant's stereo player, as it always was).
const ART_ORDER = [WH, E, MA, HP, HP_APPLE, KITCHEN];
const ART = `{% set ns = namespace(p='') %}{% for e in ${JSON.stringify(ART_ORDER).replace(/"/g, "'")} %}{% if ns.p == '' and is_state(e, 'playing') and state_attr(e, 'entity_picture') %}{% set ns.p = state_attr(e, 'entity_picture') %}{% endif %}{% endfor %}{{ ns.p }}`;
const SHOWING = { condition: 'or', conditions: PLAYERS.map(entity => ({ condition: 'state', entity, state: 'playing' })) };
const FULL_SCREEN = 'position: fixed !important; z-index: -1 !important; pointer-events: none !important; border: none !important; border-radius: 0 !important; box-shadow: none !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important; max-height: none !important;';

// Laid out like HA's media card, mirrored (Ty: "artwork on the left, controls on the right"): the material
// cover pinned to the left with its fade turned round; to its right the speaker's icon and name, the title
// over the artist (not "title - artist" on one scrolling line), then one row of previous, play, next, the
// volume slider and Stop, the shortcut shrunk to a bare icon.
const PLAYER_STYLE = {
  '.': [
    'ha-card { --mmp-unit: 40px; }',
    '.mmp-player { padding: 16px 18px 20px 196px !important; }',
    '.cover { left: 0 !important; right: auto !important; }',
    '.cover-gradient { transform: scaleX(-1); }',
    '.entity__icon { width: 24px !important; height: 24px !important; min-width: 24px !important; margin: 0 8px 0 0 !important; }',
    '.mmp-player__core { align-items: flex-start !important; }',
    '.entity__info__name { font-size: 14px !important; line-height: 24px !important; opacity: .85; }',
    '.entity__info__media { display: block !important; height: auto !important; max-height: none !important; margin: 12px 0 0 0 !important; white-space: normal !important; }',
    '.entity__info__media > div { display: none !important; }',
    '.entity__info__media > span { display: block !important; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }',
    '.attr__media_title { font-size: 19px !important; font-weight: 500 !important; line-height: 26px; color: var(--primary-text-color) !important; opacity: 1 !important; }',
    '.attr__media_artist { font-size: 14px !important; line-height: 20px; opacity: .8; }',
    '.attr__media_artist::before { content: none !important; display: none !important; }',
    '.mmp-player__adds { margin: 10px 0 0 -4px !important; display: flex !important; flex-direction: row !important; align-items: center !important; }',
    'mmp-media-controls { flex: 1 1 auto !important; flex-direction: row-reverse !important; }',
    'mmp-shortcuts { flex: 0 0 auto !important; margin: 0 !important; }',
  ].join('\n'),
  'mmp-media-controls$': '.mmp-media-controls__media { margin: 0 !important; justify-content: flex-start !important; } .mmp-media-controls__volume { flex: 1 1 auto !important; }',
  'mmp-shortcuts$': '.mmp-shortcuts__buttons { display: flex !important; } .mmp-shortcuts__button { min-height: 40px !important; height: 40px !important; width: 40px !important; min-width: 40px !important; padding: 0 !important; margin: 0 !important; background: none !important; box-shadow: none !important; border-radius: 50% !important; } .mmp-shortcuts__button .ellipsis { display: none !important; } .mmp-shortcuts__button ha-icon { margin: 0 !important; --mdc-icon-size: 26px; }',
};
const playerFor = (entity, i) => ({
  type: 'custom:mini-media-player',
  entity,
  artwork: 'material',
  info: 'scroll',
  volume_step: 5,
  hide: { power: true, source: true },
  shortcuts: { columns: 1, buttons: [{ icon: 'mdi:stop', name: 'Stop', type: 'service', id: 'script.music_stop', data: { speaker: entity } }] },
  tap_action: { action: 'navigate', navigation_path: '#music' },
  grid_options: { columns: 'full' },
  visibility: [on(entity), ...PLAYERS.slice(0, i).map(off)],
  card_mod: { style: PLAYER_STYLE },
});
const cards = PLAYERS.map(playerFor);
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

// The players sit at the foot of the left column; anything earlier (the HA media cards, the separate Stop
// button, the HomePod's stock card) is cleared out.
const mine = c => (['custom:mini-media-player', 'media-control'].includes(c.type) && PLAYERS.includes(c.entity)) || (c.type === 'button' && c.tap_action && c.tap_action.perform_action === 'script.family_room_stereo_stop');
for (const list of [left, right]) for (let i = list.length - 1; i >= 0; i--) if (mine(list[i])) list.splice(i, 1);
left.push(...cards);
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
