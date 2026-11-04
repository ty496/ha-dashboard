// Music pop-up on the Show's home view (2026-11-03), idempotently: start and pick music by touch, not only by
// voice. A centered Bubble Card pop-up (#music) like Rooms and Scores, closed by tapping outside:
// - on the left a Yet Another Media Player (HACS) player with a chip per speaker (Family Room Stereo, the
//   Whole House group, HomePod, Kitchen), its controls showing even when idle;
// - on the right a second one locked to its search sheet, opening on Music Assistant's favorites as artwork
//   tiles (the clock button shows Recently Played). The Show has no keyboard, so there the right side is for
//   browsing; typed search works from a phone, and voice covers the rest.
// Opened by a fourth pill, Music, in the bottom row, and by tapping the Now Playing player (now-playing.js).
// A /dashboard-show/music subview came first the same evening and is removed here: Ty closes the other
// screens by tapping outside them, and the Show hides a subview's back arrow.
const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, '..', 'show.json');
const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
const home = cfg.views.find(v => v.path === 'home');
const popups = home.sections.find(s => s.cards.some(c => c.card_type === 'pop-up')).cards;

const speakers = [
  ['media_player.family_room_stereo', 'Family Room'],
  ['media_player.whole_house', 'Whole House'],
  ['media_player.homepod', 'HomePod'],
  ['media_player.kitchen', 'Kitchen'],
].map(([entity_id, name]) => ({ entity_id, name, music_assistant_entity: entity_id }));

const player = {
  type: 'custom:yet-another-media-player',
  template: 'large_modern',
  entities: speakers,
  show_chip_row: 'always',
  match_theme: true,
  appearance: 'dark',
  card_height: 560,
  idle_timeout_ms: 0,
  show_player_search: false,
};
const browse = {
  type: 'custom:yet-another-media-player',
  card_type: 'search',
  entities: speakers,
  show_chip_row: 'always',
  match_theme: true,
  appearance: 'dark',
  card_height: 560,
  hide_menu_player: true,
  artwork_object_fit: 'no_artwork',
  default_search_favorites: true,
  disable_autofocus: true,
  search_view: 'card',
  search_card_columns: 3,
  pin_search_headers: true,
  show_player_search: false,
};
const music = {
  type: 'custom:bubble-card',
  card_type: 'pop-up',
  hash: '#music',
  name: 'Music',
  icon: 'mdi:music',
  popup_mode: 'centered',
  width_desktop: '1180px',
  slide_to_close: true,
  close_by_clicking_outside: true,
  cards: [{ type: 'grid', columns: 2, square: false, cards: [player, browse] }],
};
for (let i = popups.length - 1; i >= 0; i--) if (popups[i].hash === '#music') popups.splice(i, 1);
popups.push(music);
cfg.views = cfg.views.filter(v => v.path !== 'music');

// The bottom row's fourth pill.
const stack = popups.find(c => c.card_type === 'horizontal-buttons-stack');
Object.assign(stack, { '4_name': 'Music', '4_icon': 'mdi:music', '4_link': '#music', width_desktop: '720px' });

fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n');
fs.writeFileSync(path.join(__dirname, '..', 'show.min.json'), JSON.stringify(cfg));
const s = JSON.stringify(cfg); let x = 0x811c9dc5; for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 0x01000193) >>> 0; }
console.log('show.json', x.toString(16), s.length);
if (process.argv.includes('--print')) console.log(JSON.stringify({ music }));
