// Adds Now Playing for the Family Room Stereo to the Show's home view (2026-11-03), idempotently:
// - #now-playing: a Bubble Card pop-up over the dashboard for about 30 s when a new song starts on the
//   WiiM (any source: Music Assistant, voice, the WiiM app, AirPlay, Tidal Connect), on a blurred copy of
//   the album art: the cover large on the left, title, artist and album, and play/pause/skip with a
//   volume slider. It opens while input_boolean.kitchen_now_playing_popup is on (automation
//   kitchen_now_playing_popup_open) and closes when that goes off (kitchen_weather_popup_close, 30 s).
// - A compact player at the foot of the left column, under the sun and moon tiles, while the WiiM plays
//   or is paused: a small square of album art, title and artist, then a strip of controls and volume.
//   It replaced the small media-control card under the calendar (and, briefly, a big full-cover card).
// - While the WiiM plays, the whole dashboard background is a blurred copy of the album art (the
//   matt8707 community look): a fixed, full-screen markdown card behind the glass cards (z-index -1).
// Art and words read the native WiiM entity, so music started outside Music Assistant shows too.
const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, '..', 'show.json');
const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
const home = cfg.views.find(v => v.path === 'home');
const left = home.sections[0].cards;
const right = home.sections[1].cards;
const popups = home.sections.find(s => s.cards.some(c => c.card_type === 'pop-up')).cards;

const E = 'media_player.family_room_family_room_wiim';
// Music Assistant's player for the same WiiM: while MA streams, only it can skip (the WiiM's own entity
// drops next and previous), so controls use it whenever it is playing or paused, and the WiiM's otherwise.
const MA = 'media_player.family_room_stereo';
const MA_ON = { condition: 'state', entity: MA, state: ['playing', 'paused'] };
const MA_OFF = { condition: 'state', entity: MA, state_not: ['playing', 'paused'] };
const HELPER = 'input_boolean.kitchen_now_playing_popup';
const NOT_A_CARD = 'ha-card { background: none !important; border: none !important; box-shadow: none !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important; }';

const cover = {
  type: 'markdown',
  content: `{% set p = state_attr('${E}', 'entity_picture') %}{% if p %}<img src="{{ p }}">{% endif %}`,
  card_mod: { style: {
    '.': NOT_A_CARD + ' ha-card { padding: 0 !important; }',
    'ha-markdown$': 'img { display: block; width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 24px; box-shadow: 0 22px 60px rgba(0, 0, 0, 0.5); }',
  } },
};
const words = {
  type: 'markdown',
  content: [
    `## {{ state_attr('${E}', 'media_title') or 'Nothing playing' }}`,
    `### {{ state_attr('${E}', 'media_artist') or '' }}`,
    `{{ state_attr('${E}', 'media_album_name') or '' }}`,
  ].join('\n'),
  card_mod: { style: {
    '.': NOT_A_CARD + ' ha-card { padding: 28px 8px 8px 8px !important; }',
    'ha-markdown$': 'h2 { font-size: 46px !important; line-height: 1.1 !important; font-weight: 700 !important; margin: 0 0 12px 0 !important; color: #fff !important; text-shadow: 0 2px 12px rgba(0,0,0,.45); } h3 { font-size: 30px; font-weight: 500; margin: 0 0 10px 0; color: rgba(255,255,255,.88); } p { font-size: 22px; color: rgba(255,255,255,.7); margin: 0; }',
  } },
};
const controlsFor = (entity) => ({
  type: 'custom:mini-media-player',
  entity,
  artwork: 'none',
  volume_step: 5,
  hide: { name: true, icon: true, info: true, power: true, source: true, progress: false, volume: false, mute: false, prev: false, next: false },
  card_mod: { style: NOT_A_CARD + ' ha-card { --mmp-text-color: #fff; --mmp-icon-color: #fff; --mmp-accent-color: #fff; --mmp-button-size: 56px; padding: 8px !important; }' },
});
const controls = [
  { type: 'conditional', conditions: [MA_ON], card: controlsFor(MA) },
  { type: 'conditional', conditions: [MA_OFF], card: controlsFor(E) },
];
const popup = {
  type: 'custom:bubble-card',
  card_type: 'pop-up',
  hash: '#now-playing',
  name: 'Now playing',
  icon: 'mdi:music',
  popup_mode: 'centered',
  width_desktop: '1180px',
  slide_to_close: true,
  close_by_clicking_outside: true,
  trigger_entity: HELPER,
  trigger_state: 'on',
  trigger_close: true,
  close_action: { action: 'perform-action', perform_action: 'input_boolean.turn_off', target: { entity_id: HELPER } },
  styles: [
    '.bubble-pop-up { overflow: hidden !important; }',
    `.bubble-pop-up-background { background: center / cover no-repeat url('\${hass.states['${E}'].attributes.entity_picture || ''}') !important; filter: blur(44px) saturate(1.35) brightness(0.62) !important; transform: scale(1.25); opacity: 1 !important; }`,
  ].join('\n'),
  cards: [{ type: 'horizontal-stack', cards: [cover, { type: 'vertical-stack', cards: [words, ...controls] }] }],
};
const playerFor = (entity, visibility) => ({
  type: 'custom:mini-media-player',
  entity,
  artwork: 'default',
  info: 'scroll',
  volume_step: 5,
  hide: { power: true, source: true, name: true },
  grid_options: { columns: 'full' },
  visibility,
  card_mod: { style: 'ha-card { border-radius: 24px; --mmp-unit: 36px; } .entity__artwork, .entity__icon { width: 60px !important; height: 60px !important; min-width: 60px !important; border-radius: 12px !important; background-size: cover !important; } .entity__info__media, .entity__info__media span { font-size: 18px !important; font-weight: 600 !important; color: var(--primary-text-color) !important; opacity: 1 !important; }' },
});
const cards = [
  playerFor(MA, [MA_ON]),
  playerFor(E, [{ condition: 'state', entity: E, state: ['playing', 'paused'] }, MA_OFF]),
];
const backdrop = {
  type: 'markdown',
  name: 'Now playing background',
  content: ' ',
  visibility: [{ condition: 'state', entity: E, state: 'playing' }],
  card_mod: { style: `ha-card { position: fixed !important; top: -80px !important; left: -80px !important; width: calc(100vw + 160px) !important; height: calc(100vh + 160px) !important; max-height: none !important; z-index: -1 !important; pointer-events: none !important; border: none !important; border-radius: 0 !important; box-shadow: none !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important; background: center / cover no-repeat url('{{ state_attr('${E}', 'entity_picture') or '' }}') !important; filter: blur(40px) saturate(1.3) brightness(0.55); }` },
};

// The old small control under the calendar goes; the player sits at the foot of the left column.
const old = right.findIndex(c => c.type === 'media-control' && c.entity === E);
if (old >= 0) right.splice(old, 1);
for (const list of [left, right]) for (let i = list.length - 1; i >= 0; i--) if (list[i].type === 'custom:mini-media-player' && [E, MA].includes(list[i].entity)) list.splice(i, 1);
left.push(...cards);

const bg = popups.findIndex(c => c.name === 'Now playing background');
if (bg >= 0) popups[bg] = backdrop; else popups.push(backdrop);

const at = popups.findIndex(c => c.hash === '#now-playing');
if (at >= 0) popups[at] = popup; else popups.push(popup);

fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n');
fs.writeFileSync(path.join(__dirname, '..', 'show.min.json'), JSON.stringify(cfg));
const s = JSON.stringify(cfg); let x = 0x811c9dc5; for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 0x01000193) >>> 0; }
console.log('show.json', x.toString(16), s.length);
if (process.argv.includes('--print')) console.log(JSON.stringify({ cards, backdrop }));
