// Music pop-up on the Show's home view (2026-11-03), idempotently: start and pick music by touch, not only by
// voice. A centered Bubble Card pop-up (#music) like Rooms and Scores, closed by tapping outside:
// - on the left a Yet Another Media Player (HACS) player with a chip per speaker (Family Room Stereo, the
//   Whole House group, HomePod, Kitchen), its controls showing even when idle;
// - on the right a second one locked to its search sheet, opening on Music Assistant's favorites as artwork
//   tiles (the clock button shows Recently Played), following the player's speaker. The Show has no
//   keyboard, so the right side is for browsing; voice covers search.
// Opened by a fourth pill, Music, in the bottom row, and by tapping the Now Playing player (now-playing.js).
// A /dashboard-show/music subview came first the same evening and is removed here: Ty closes the other
// screens by tapping outside them, and the Show hides a subview's back arrow.
const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, '..', 'show.json');
const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
const home = cfg.views.find(v => v.path === 'home');
const popups = home.sections.find(s => s.cards.some(c => c.card_type === 'pop-up')).cards;

const SPEAKERS = [
  ['media_player.family_room_stereo', 'Family Room'],
  ['media_player.whole_house', 'Whole House'],
  ['media_player.homepod', 'HomePod'],
  ['media_player.kitchen', 'Kitchen'],
];
// The Whole House group's members are never picked automatically: while the group plays, YAMP otherwise jumps
// to its sync leader (the Kitchen Echo), and the header showed Kitchen instead of Whole House.
const GROUP_MEMBERS = ['media_player.homepod', 'media_player.kitchen'];
const speakers = SPEAKERS.map(([entity_id, name]) => ({ entity_id, name, music_assistant_entity: entity_id, ...(GROUP_MEMBERS.includes(entity_id) ? { disable_auto_select: true } : {}) }));
// One speaker choice for both cards: each writes its chosen speaker to input_text.music_speaker (a helper
// made for this) and follows it, so a playlist tapped on the right plays where the left card points.
const SYNC = { sync_entity_type: 'yamp_playback_entity', sync_entity_helper: 'input_text.music_speaker', in_menu: 'hidden', card_trigger: 'none' };
// select_entity also names the helper as its entity: YAMP 2026.11.0 re-renders on a change only for the
// entities its actions name there, so without it the player card never noticed the header's choice.
const actions = [{ action: 'sync_selected_entity', ...SYNC }, { action: 'select_entity', ...SYNC, entity: 'input_text.music_speaker' }];

// Dressed like the rest of the Show (Ty: the card's own orange chips "don't match the overall aesthetic"):
// chips are the bottom row's pills (navy glass, a thin near-white border, white text), the chosen one solid
// white; the accent is the theme's light blue rather than its orange.
const DRESS = [
  'ha-card { --custom-accent: #7cc4ff; --yamp-chip-bg: rgba(20, 26, 43, 0.72); --yamp-chip-text: #f2f4f8; --yamp-chip-selected-bg: #f2f4f8; --yamp-chip-selected-text: #141a2b; }',
  '.chip { background: rgba(20, 26, 43, 0.72) !important; border: 1px solid rgba(242, 244, 248, 0.9) !important; color: #f2f4f8 !important; box-shadow: none !important; font-size: 14px !important; font-weight: 400 !important; -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px); }',
  '.chip[selected] { background: #f2f4f8 !important; color: #141a2b !important; }',
  '.chip ha-icon, .chip .chip-icon { color: inherit !important; }',
].join(' ');
// Neither card shows its own speaker chips: the pop-up's header picks the speaker for both. The search card
// has no search box either (the Show has no keyboard).
const NO_SPEAKER_CHIPS = ' .chip-row:not(.search-filter-chips) { display: none !important; }';
const BROWSE_DRESS = DRESS + NO_SPEAKER_CHIPS + ' .entity-options-search-row { display: none !important; }';
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
  actions,
  card_mod: { style: DRESS + NO_SPEAKER_CHIPS },
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
  actions,
  card_mod: { style: BROWSE_DRESS },
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
  // The speaker picker, right of the title, works like a device picker: script.music_speaker_select writes the
  // speaker to input_text.music_speaker, which both cards follow (and write back when playback moves the player
  // to another speaker), and moves what was playing on the previous speaker there. Same pills as the chips,
  // the chosen one solid white.
  sub_button: SPEAKERS.map(([entity_id, name]) => ({
    name, icon: entity_id === 'media_player.whole_house' ? 'mdi:speaker-multiple' : 'mdi:speaker', show_name: true, show_icon: true, show_background: false,
    tap_action: { action: 'perform-action', perform_action: 'script.music_speaker_select', data: { speaker: entity_id } },
  })),
  styles: [
    '.bubble-sub-button { background: rgba(20, 26, 43, 0.72) !important; border: 1px solid rgba(242, 244, 248, 0.9) !important; color: #f2f4f8 !important; border-radius: 24px !important; height: 40px !important; padding: 0 14px !important; font-size: 14px !important; font-weight: 400 !important; }',
    '.bubble-sub-button ha-icon { color: inherit !important; }',
    ...SPEAKERS.map(([entity_id], i) => `.bubble-sub-button-${i + 1} { \${hass.states['input_text.music_speaker']?.state === '${entity_id}' ? 'background: #f2f4f8 !important; color: #141a2b !important;' : ''} }`),
  ].join('\n'),
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
