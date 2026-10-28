// Generates themes/show_glass.yaml: "liquid glass" themes for the Show dashboard.
// Each theme = a full-view background (photo under a readability scrim) + a glass card family.
// Backgrounds live in www/bg (served by HA at /local/bg); see README for the delivery route.
const fs = require('fs');

// Glass recipe (2026-10-27): clearer than the first pass, iOS-style. Low blur so the scene
// shows through, a hairline top highlight, and a bright specular rim along the bottom edge
// done with inset box-shadows (ha-card honours --ha-card-box-shadow and --ha-card-backdrop-filter).
const glass = (bg, border, top, rim, glow, drop) => ({
  'ha-card-background': bg,
  'ha-card-backdrop-filter': 'blur(14px) saturate(150%)',
  'ha-card-border-width': '1px',
  'ha-card-border-color': border,
  'ha-card-border-radius': '24px',
  'ha-card-box-shadow': `inset 0 1px 0 ${top}, inset 0 -1px 0 ${rim}, inset 0 -10px 18px -14px ${glow}, 0 10px 30px ${drop}`,
});

const light = {
  ...glass('rgba(255, 255, 255, 0.34)', 'rgba(255, 255, 255, 0.65)', 'rgba(255, 255, 255, 0.75)', 'rgba(255, 255, 255, 0.60)', 'rgba(255, 255, 255, 0.90)', 'rgba(31, 38, 135, 0.14)'),
  'card-background-color': '#ffffff',
  'primary-text-color': '#1b2230',
  'secondary-text-color': '#4a5568',
  'disabled-text-color': '#94a0b2',
  'text-primary-color': '#ffffff',
  'primary-color': '#0a6fd6',
  'accent-color': '#ff7a45',
  'state-icon-color': '#4a5568',
  'state-icon-active-color': '#f5a623',
  'divider-color': 'rgba(0, 0, 0, 0.08)',
  'outline-color': 'rgba(0, 0, 0, 0.12)',
  'secondary-background-color': 'rgba(255, 255, 255, 0.30)',
  'app-header-background-color': 'rgba(255, 255, 255, 0.30)',
  'app-header-text-color': '#1b2230',
  'sidebar-background-color': 'rgba(255, 255, 255, 0.55)',
  'sidebar-text-color': '#4a5568',
  'sidebar-icon-color': '#4a5568',
  'sidebar-selected-text-color': '#0a6fd6',
  'sidebar-selected-icon-color': '#0a6fd6',
  'switch-checked-color': '#0a6fd6',
  'switch-unchecked-button-color': '#ffffff',
  'switch-unchecked-track-color': 'rgba(0, 0, 0, 0.25)',
  'input-fill-color': 'rgba(255, 255, 255, 0.4)',
  'input-ink-color': '#1b2230',
  'input-label-ink-color': '#4a5568',
};

const dark = {
  ...glass('rgba(255, 255, 255, 0.12)', 'rgba(255, 255, 255, 0.28)', 'rgba(255, 255, 255, 0.22)', 'rgba(255, 255, 255, 0.30)', 'rgba(255, 255, 255, 0.50)', 'rgba(0, 0, 0, 0.30)'),
  'card-background-color': '#141a2b',
  'primary-text-color': '#f2f4f8',
  'secondary-text-color': '#b4bccb',
  'disabled-text-color': '#6c7786',
  'text-primary-color': '#0b0e1a',
  'primary-color': '#7cc4ff',
  'accent-color': '#ffb070',
  'state-icon-color': '#b4bccb',
  'state-icon-active-color': '#ffd166',
  'divider-color': 'rgba(255, 255, 255, 0.10)',
  'outline-color': 'rgba(255, 255, 255, 0.14)',
  'secondary-background-color': 'rgba(255, 255, 255, 0.06)',
  'app-header-background-color': 'rgba(0, 0, 0, 0.25)',
  'app-header-text-color': '#f2f4f8',
  'sidebar-background-color': 'rgba(0, 0, 0, 0.35)',
  'sidebar-text-color': '#b4bccb',
  'sidebar-icon-color': '#b4bccb',
  'sidebar-selected-text-color': '#7cc4ff',
  'sidebar-selected-icon-color': '#7cc4ff',
  'switch-checked-color': '#7cc4ff',
  'switch-unchecked-button-color': '#b4bccb',
  'switch-unchecked-track-color': 'rgba(255, 255, 255, 0.25)',
  'input-fill-color': 'rgba(255, 255, 255, 0.06)',
  'input-ink-color': '#f2f4f8',
  'input-label-ink-color': '#b4bccb',
  'map-filter': 'invert(.9) hue-rotate(170deg) brightness(1.5) contrast(1.2) saturate(.3)',
};

// Background set. "strip" = the comic-strip beagle scenes (chosen 2026-10-27); the alpine photos
// (dawn.jpg ... night.jpg) are still in www/bg if the set is ever swapped back.
const IMG = '/local/bg';
const scrimLight = 'linear-gradient(rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.06))';
const scrimDark  = 'linear-gradient(rgba(5, 8, 20, 0.08), rgba(5, 8, 20, 0.26))';
// Sized by width, with the scene's own sky colour (sampled from the top edge of the image) filling
// anything above or below it. The vertical offset centres the image in the first screen: the image
// is 100vw wide and 1.6:1, so its centre lands at 50vh when its top sits at 50vh - 31.25vw. On the
// 16:10 Show that is 0, i.e. exactly cover. On a portrait phone the scene starts centred and, since
// HA's view background is position: absolute inside the scrolling view, it scrolls away with the
// cards (1:1, the closest CSS alone gets to parallax) with sky colour above and below.
// 2026-10-27: the centred offset (center calc(50vh - 31.25vw)) read as "stuck" on Ty's iPhone, so
// the scene is anchored to the bottom of the view again, which he preferred.
// 2026-10-27 (evening): the word "fixed" in the string makes HA's hui-view-background switch to
// position: fixed (it checks for the token and applies its own Safari-iOS hack), so on the phone the
// scene now stays still at the bottom of the viewport while the buttons scroll over it. No change on
// the Show, where the image already covered the screen exactly.
// The token must stand alone: the frontend splits on spaces and compares whole words, so "fixed,"
// (followed by the next layer's comma) does not count. Hence fixed before no-repeat.
// Above the image (only visible on tall viewports) a transparent tile repeats so the sky keeps
// going: stars for night/halloween, a few pale stars for dusk, rain lines for rain. Tiles are
// drawn by www/bg/make_tiles.ps1 in the strip's flat style. Day skies stay plain.
const photo = (file, scrim, sky, tile) => `${scrim}, url('${IMG}/${file}.jpg') center bottom / 100% auto fixed no-repeat` +
  (tile ? `, url('${IMG}/${tile.file}') center top / ${tile.size} auto repeat` : '') + `, ${sky}`;
const sky = { dawn: '#fcc6b2', day: '#96d3f0', cloudy: '#b8b8ba', rain: '#617b8e', dusk: '#80647a', night: '#132e48', halloween: '#2b4b73',
  thanksgiving: '#efad56', christmas: '#37608f', christmasDay: '#aed6e5' };
const stars = { file: 'stars.png', size: '360px' };
const snow = { file: 'snow.png', size: '300px' };
const themes = {
  'Glass Dawn':      { base: light, bg: photo('strip-dawn', scrimLight, sky.dawn),          primary: sky.dawn },
  'Glass Day':       { base: light, bg: photo('strip-day', scrimLight, sky.day),            primary: sky.day },
  'Glass Cloudy':    { base: light, bg: photo('strip-cloudy', scrimLight, sky.cloudy),      primary: sky.cloudy },
  'Glass Rain':      { base: dark,  bg: photo('strip-rain', scrimDark, sky.rain, { file: 'rain.png', size: '300px' }),       primary: sky.rain },
  'Glass Dusk':      { base: dark,  bg: photo('strip-dusk', scrimDark, sky.dusk, { file: 'stars-dusk.png', size: '360px' }), primary: sky.dusk },
  'Glass Night':     { base: dark,  bg: photo('strip-night', scrimDark, sky.night, stars),         primary: sky.night },
  'Glass Halloween': { base: dark,  bg: photo('strip-halloween', scrimDark, sky.halloween, stars), primary: sky.halloween },
  // Holiday scenes, picked by date windows in the automation (see automations/show_glass_follows_the_sky.json).
  'Glass Thanksgiving':  { base: light, bg: photo('strip-thanksgiving', scrimLight, sky.thanksgiving),      primary: sky.thanksgiving },
  'Glass Christmas':     { base: dark,  bg: photo('strip-christmas', scrimDark, sky.christmas, snow),        primary: sky.christmas },
  'Glass Christmas Day': { base: light, bg: photo('strip-christmas-day', scrimLight, sky.christmasDay, snow), primary: sky.christmasDay },
};

let out = '# Liquid-glass themes for the Show dashboard. GENERATED by build_glass.js, edit that.\n' +
          '# Backgrounds are images in /config/www/bg (served at /local/bg), see README.\n' +
          '# Picked by the "Show glass follows the sky" automation from sun elevation + weather.\n\n';
for (const [name, t] of Object.entries(themes)) {
  out += `${name}:\n`;
  out += `  lovelace-background: "${t.bg}"\n`;
  out += `  primary-background-color: "${t.primary}"\n`;
  for (const [k, v] of Object.entries(t.base)) out += `  ${k}: "${v}"\n`;
  out += '\n';
}
fs.writeFileSync(__dirname + '/show_glass.yaml', out);
console.log('wrote show_glass.yaml', out.length, 'bytes,', Object.keys(themes).length, 'themes');
