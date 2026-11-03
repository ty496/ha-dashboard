// Adds the weather pop-ups to the Show's home view (2026-11-03), idempotently: Bubble Card pop-ups with the
// hourly forecast (and the current conditions) over the week's daily one.
// - #weather: home (weather.forecast_home). Opens when input_boolean.kitchen_weather_popup turns on, which
//   voice_weather_local does when the Kitchen Echo asks about home weather.
// - #place-weather: the last place Claude looked up (weather.place_weather, from the place_weather
//   integration, named after the place). Opens when input_boolean.kitchen_place_weather_popup turns on,
//   which kitchen_place_weather_popup_open does on place_weather_shown from the Kitchen Echo.
// Each closes when its helper turns off (kitchen_weather_popup_close, 30 s later); closing one by hand
// turns its helper off too, so the next question opens it again.
const fs = require('fs');
const path = require('path');
const file = path.join(__dirname, '..', 'show.json');
const cfg = JSON.parse(fs.readFileSync(file, 'utf8'));
const popups = cfg.views.find(v => v.path === 'home').sections.find(s => s.cards.some(c => c.card_type === 'pop-up')).cards;

const popup = (hash, entity, helper) => ({
  type: 'custom:bubble-card',
  card_type: 'pop-up',
  hash,
  name: 'Weather',
  icon: 'mdi:weather-partly-cloudy',
  popup_mode: 'centered',
  width_desktop: '820px',
  slide_to_close: true,
  close_by_clicking_outside: true,
  trigger_entity: helper,
  trigger_state: 'on',
  trigger_close: true,
  close_action: { action: 'perform-action', perform_action: 'input_boolean.turn_off', target: { entity_id: helper } },
  cards: [
    { type: 'weather-forecast', entity, show_current: true, show_forecast: true,
      forecast_type: 'hourly', forecast_slots: 8, secondary_info_attribute: 'wind_speed' },
    { type: 'weather-forecast', entity, show_current: false, show_forecast: true,
      forecast_type: 'daily', forecast_slots: 7 },
  ],
});
const cards = [
  popup('#weather', 'weather.forecast_home', 'input_boolean.kitchen_weather_popup'),
  popup('#place-weather', 'weather.place_weather', 'input_boolean.kitchen_place_weather_popup'),
];

for (const card of cards) {
  const at = popups.findIndex(c => c.hash === card.hash);
  if (at >= 0) popups[at] = card; else popups.push(card);
}
fs.writeFileSync(file, JSON.stringify(cfg, null, 2) + '\n');
if (process.argv.includes('--print')) console.log(JSON.stringify(cards[1]));
