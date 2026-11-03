// Adds the #weather pop-up to the Show's home view (2026-11-03), idempotently: a Bubble Card pop-up with
// today's hourly forecast (and the current conditions) over the week's daily one, both weather.forecast_home.
// It opens when input_boolean.kitchen_weather_popup turns on (the voice_weather_local automation does that
// when the Kitchen Echo asks about home weather) and closes when it turns off (kitchen_weather_popup_close,
// 30 s later). Closing it by hand turns the helper off too, so the next question opens it again.
const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, '..', 'show.json');
const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
const popups = cfg.views.find(v => v.path === 'home').sections.find(s => s.cards.some(c => c.card_type === 'pop-up')).cards;

const HELPER = 'input_boolean.kitchen_weather_popup';
const weather = {
  type: 'custom:bubble-card',
  card_type: 'pop-up',
  hash: '#weather',
  name: 'Weather',
  icon: 'mdi:weather-partly-cloudy',
  popup_mode: 'centered',
  width_desktop: '820px',
  slide_to_close: true,
  close_by_clicking_outside: true,
  trigger_entity: HELPER,
  trigger_state: 'on',
  trigger_close: true,
  close_action: { action: 'perform-action', perform_action: 'input_boolean.turn_off', target: { entity_id: HELPER } },
  cards: [
    { type: 'weather-forecast', entity: 'weather.forecast_home', show_current: true, show_forecast: true,
      forecast_type: 'hourly', forecast_slots: 8, secondary_info_attribute: 'wind_speed' },
    { type: 'weather-forecast', entity: 'weather.forecast_home', show_current: false, show_forecast: true,
      forecast_type: 'daily', forecast_slots: 7 },
  ],
};

const at = popups.findIndex(c => c.hash === '#weather');
if (at >= 0) popups[at] = weather; else popups.push(weather);
fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n');
if (process.argv.includes('--print')) console.log(JSON.stringify(weather));
