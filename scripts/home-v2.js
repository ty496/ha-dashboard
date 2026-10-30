// Rewrites the Show dashboard's home view (2026-10-30): the screen is clock, weather, calendar and
// live events; the smart controls move into Bubble Card pop-ups opened from a bottom button bar.
// One-shot: run once against the pre-2026-10-30 show.json (it picks the old cards by name). Kept for the record.
const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, '..', 'show.json');
const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
const home = cfg.views.find(v => v.path === 'home');
const old = {};
home.sections.forEach(s => s.cards.forEach(c => {
  const key = c.name || c.area || c.entity || c.type;
  old[key] = c;
}));
const pick = k => { if (!old[k]) throw new Error('missing card ' + k); return old[k]; };

const quick = ['Everything off', 'Evening lamps', 'Coffee bar', 'Patio light', 'Bathroom glow', 'TV backlight']
  .map(k => ({ ...pick(k), grid_options: { columns: 4, rows: 2 } }));
const rooms = ['living_room', 'family_room', 'kitchen', 'basement', 'primary', 'garage'].map(pick);
const teams = ['broncos', 'bears', 'avalanche', 'fsu', 'iowa', 'rockies'];
const live = teams.map(t => ({
  type: 'conditional',
  conditions: [{ condition: 'state', entity: `sensor.${t}`, state: 'IN' }],
  card: { type: 'custom:teamtracker-card', entity: `sensor.${t}`, grid_options: { columns: 'full' } },
}));
const calendar = pick('This week');
const calColor = { 'calendar.home': 'home', 'calendar.personal': 'personal', 'calendar.olive': 'olive',
  'calendar.travel': 'travel', 'calendar.birthdays': 'birthdays', 'calendar.ty_mercer90_gmail_com': 'gmail' };
calendar.entities.forEach(e => { e.color = `var(--show-cal-${calColor[e.entity]})`; });
calendar.maxDaysToShow = 10;
calendar.grid_options = { columns: 'full' };

const popup = (hash, name, icon, cards) => ({
  type: 'custom:bubble-card', card_type: 'pop-up', hash, name, icon,
  popup_mode: 'centered', width_desktop: '820px', slide_to_close: true, close_by_clicking_outside: true,
  cards,
});
const grid = (cards, columns) => ({ type: 'grid', columns, square: false, cards });

home.sections = [
  {
    type: 'grid', column_span: 1,
    cards: [
      pick('clock'),
      pick('Wheat Ridge'),
      { ...pick('Sunrise') }, { ...pick('Sunset') }, { ...pick('Moon') },
    ],
  },
  {
    type: 'grid', column_span: 2,
    cards: [
      {
        type: 'markdown',
        title: 'Needs attention',
        content: '**{{ states("sensor.broken_automations") }} automation(s) unavailable:** {{ states("sensor.broken_automation_names") }}',
        grid_options: { columns: 'full' },
        visibility: [{ condition: 'numeric_state', entity: 'sensor.broken_automations', above: 0 }],
      },
      ...live,
      calendar,
      ...['media_player.family_room_family_room_wiim', 'media_player.family_room_family_room_homepod', 'media_player.basement_receiver'].map(pick),
    ],
  },
  {
    type: 'grid', column_span: 3,
    cards: [
      popup('#controls', 'Quick actions', 'mdi:lightning-bolt-outline', [grid(quick, 3)]),
      popup('#rooms', 'Rooms', 'mdi:floor-plan', [grid(rooms, 2)]),
      popup('#scores', 'Scores', 'mdi:scoreboard-outline', [grid(teams.map(t => ({ type: 'custom:teamtracker-card', entity: `sensor.${t}` })), 2)]),
      {
        type: 'custom:bubble-card', card_type: 'horizontal-buttons-stack',
        width_desktop: '540px', is_sidebar_hidden: true, rise_animation: false, highlight_current_view: true, hide_gradient: true,
        '1_name': 'Quick actions', '1_icon': 'mdi:lightning-bolt-outline', '1_link': '#controls',
        '2_name': 'Rooms', '2_icon': 'mdi:floor-plan', '2_link': '#rooms',
        '3_name': 'Scores', '3_icon': 'mdi:scoreboard-outline', '3_link': '#scores',
      },
    ],
  },
];

fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n');
fs.writeFileSync(path.join(__dirname, '..', 'show.min.json'), JSON.stringify(cfg));
console.log('home view rewritten:', home.sections.map(s => s.cards.length + ' cards').join(', '));
