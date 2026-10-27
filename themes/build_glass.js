// Generates themes/show_glass.yaml: six "liquid glass" themes for the Show dashboard.
// Each theme = a background (CSS gradient for now, image later) + a glass card family.
const fs = require('fs');

const light = {
  'ha-card-background': 'rgba(255, 255, 255, 0.55)',
  'card-background-color': 'rgba(255, 255, 255, 0.55)',
  'ha-card-backdrop-filter': 'blur(24px) saturate(160%)',
  'ha-card-border-width': '1px',
  'ha-card-border-color': 'rgba(255, 255, 255, 0.75)',
  'ha-card-border-radius': '24px',
  'ha-card-box-shadow': '0 8px 32px rgba(31, 38, 135, 0.12)',
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
  'secondary-background-color': 'rgba(255, 255, 255, 0.35)',
  'app-header-background-color': 'rgba(255, 255, 255, 0.35)',
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
  'ha-card-background': 'rgba(255, 255, 255, 0.10)',
  'card-background-color': 'rgba(255, 255, 255, 0.10)',
  'ha-card-backdrop-filter': 'blur(24px) saturate(160%)',
  'ha-card-border-width': '1px',
  'ha-card-border-color': 'rgba(255, 255, 255, 0.18)',
  'ha-card-border-radius': '24px',
  'ha-card-box-shadow': '0 8px 32px rgba(0, 0, 0, 0.35)',
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

// Backgrounds. `lovelace-background` paints the whole view; the base colour sits behind the
// gradients so the page is never white while fonts load.
const themes = {
  'Glass Dawn': { base: light, bg:
    'radial-gradient(70% 60% at 20% 85%, #ffb37a 0%, rgba(255, 179, 122, 0) 60%), ' +
    'radial-gradient(60% 50% at 80% 15%, #8ec5ff 0%, rgba(142, 197, 255, 0) 60%), ' +
    'linear-gradient(180deg, #fde3c8 0%, #d7e8ff 100%)', primary: '#fde3c8' },
  'Glass Day': { base: light, bg:
    'radial-gradient(60% 55% at 75% 10%, #ffffff 0%, rgba(255, 255, 255, 0) 55%), ' +
    'radial-gradient(70% 60% at 15% 95%, #9fe0ff 0%, rgba(159, 224, 255, 0) 60%), ' +
    'linear-gradient(180deg, #4f9fe8 0%, #bfe0ff 100%)', primary: '#4f9fe8' },
  'Glass Cloudy': { base: light, bg:
    'radial-gradient(60% 50% at 30% 25%, #f6f8fb 0%, rgba(246, 248, 251, 0) 60%), ' +
    'radial-gradient(50% 45% at 85% 80%, #c3d0dd 0%, rgba(195, 208, 221, 0) 60%), ' +
    'linear-gradient(180deg, #a9b8c8 0%, #e6ebf0 100%)', primary: '#a9b8c8' },
  'Glass Rain': { base: dark, bg:
    'radial-gradient(60% 50% at 70% 15%, #5b7ea8 0%, rgba(91, 126, 168, 0) 60%), ' +
    'radial-gradient(50% 45% at 15% 85%, #2d4a6e 0%, rgba(45, 74, 110, 0) 60%), ' +
    'linear-gradient(180deg, #16223a 0%, #34485f 100%)', primary: '#16223a' },
  'Glass Dusk': { base: dark, bg:
    'radial-gradient(55% 50% at 28% 72%, #e23cf0 0%, rgba(226, 60, 240, 0) 60%), ' +
    'radial-gradient(45% 45% at 58% 78%, #ff9a7a 0%, rgba(255, 154, 122, 0) 55%), ' +
    'radial-gradient(40% 40% at 92% 12%, #2b5bff 0%, rgba(43, 91, 255, 0) 55%), ' +
    'linear-gradient(180deg, #070a1e 0%, #0d1030 100%)', primary: '#070a1e' },
  'Glass Night': { base: dark, bg:
    'radial-gradient(50% 45% at 18% 18%, #2a2f6e 0%, rgba(42, 47, 110, 0) 60%), ' +
    'radial-gradient(45% 40% at 85% 82%, #4b1d6b 0%, rgba(75, 29, 107, 0) 60%), ' +
    'linear-gradient(180deg, #05070f 0%, #0a0d1c 100%)', primary: '#05070f' },
};

let out = '# Liquid-glass themes for the Show dashboard. GENERATED by build_glass.js, edit that.\n' +
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
