# ha-dashboard

Home Assistant wall dashboard for the Echo Show 8 (2nd gen, 1280x800).

- `show.json` is the source of truth (pretty-printed). `show.min.json` is the same thing minified for pasting.
- Live copy: HA storage dashboard `/dashboard-show` ("Show"). Views: `home` plus subviews `living-room`, `family-room`, `kitchen`, `basement`, `primary`, `outside`.
- Native HA 2026.10 cards only. No HACS cards required. Kiosk Mode (HACS) is optional and only hides the header/sidebar: open `/dashboard-show/home?kiosk` on the Show.

## Deploy

From a signed-in HA tab, in the browser console (or the Claude in Chrome JS tool):

```js
const h = document.querySelector('home-assistant').hass;
const cfg = /* paste show.min.json */;
await h.callWS({type: 'lovelace/config/save', url_path: 'dashboard-show', config: cfg});
```

If the dashboard does not exist yet:

```js
await h.callWS({type: 'lovelace/dashboards/create', url_path: 'dashboard-show', title: 'Show',
  icon: 'mdi:tablet-dashboard', show_in_sidebar: true, require_admin: false, mode: 'storage'});
```

Read the live config back with `h.callWS({type: 'lovelace/config', url_path: 'dashboard-show'})`.

## Edit

Edit `show.json`, then regenerate the minified copy:

```sh
node -e "const c=require('./show.json'); require('fs').writeFileSync('show.min.json', JSON.stringify(c))"
```

## Entities it depends on

Everything comes through the Hubitat integration (Maker API 144) except: `sensor.sunrise_time` and `sensor.sunset_time` (Template helpers, `%-I:%M %p` of sun.sun next_rising/next_setting), `sensor.moon_phase` (Moon integration), `weather.forecast_home` (met.no), `calendar.household` (Local Calendar), `todo.shopping_list`, `media_player.family_room_family_room_wiim` (WiiM), `media_player.family_room_family_room_homepod` (Apple TV integration), `media_player.basement_receiver` (Denon), `media_player.shield` and `media_player.65q750g` (Cast). If an entity id changes in HA, search this file for the old id.

## Themes

`themes/show_day_night.yaml` defines **Day** and **Night**. HA loads it from `/config/themes/show_day_night.yaml`. The automation `show_theme_follows_sun` (built in the HA UI, visible under Settings > Automations) switches the backend default theme at sunrise+20 min and sunset-20 min and on HA start.

To ship a theme edit: push the file to the gist (`gh gist edit 968384ee80f15192fe5b25e54ffe2238 themes/show_day_night.yaml`), then in the HA tab:

```js
await h.callService('downloader','download_file',{url:'https://gist.githubusercontent.com/ty496/968384ee80f15192fe5b25e54ffe2238/raw/show_day_night.yaml',subdir:'themes',filename:'show_day_night.yaml',overwrite:true});
await h.callService('frontend','reload_themes',{});
await h.callService('automation','trigger',{entity_id:'automation.show_theme_follows_the_sun'});
```

## Glass themes (liquid glass + sky backgrounds)

`themes/show_glass.yaml` is **generated** by `node themes/build_glass.js`. It defines six themes, each a full-view background (`lovelace-background`, painted by HA's `hui-view-background`) plus a glass card family (`ha-card-background` translucent white, `ha-card-backdrop-filter: blur(24px) saturate(160%)`, 1px translucent border, 24px radius): **Glass Dawn**, **Glass Day**, **Glass Cloudy** (light glass, dark text) and **Glass Rain**, **Glass Dusk**, **Glass Night** (dark glass, light text). Backgrounds are CSS gradients for now; swap any `bg` for `center / cover no-repeat url('/local/bg/<file>.jpg') fixed` once images live in `/config/www/bg/`.

`automations/show_glass_follows_the_sky.json` (HA id `show_glass_follows_the_sky`) picks the theme every 10 minutes, on weather or sun change and on HA start: elevation < -6 → Night; < 8 → Dawn if rising else Dusk; else rainy family → Rain, cloudy family → Cloudy, otherwise Day. It replaced `show_theme_follows_sun`, which is left in HA but turned off.

Ship a theme edit: `node themes/build_glass.js`, then `gh gist edit 968384ee80f15192fe5b25e54ffe2238 themes/show_glass.yaml` (first time: `--add`), then in the HA tab:

```js
await h.callService('downloader','download_file',{url:'https://gist.githubusercontent.com/ty496/968384ee80f15192fe5b25e54ffe2238/raw/show_glass.yaml',subdir:'themes',filename:'show_glass.yaml',overwrite:true});
await h.callService('frontend','reload_themes',{});
await h.callService('automation','trigger',{entity_id:'automation.show_glass_follows_the_sky'});
```

Open browsers need a reload to pick up a theme change. Kiosk Mode (HACS) is installed: `/dashboard-show/home?kiosk` hides header and sidebar.

### Backgrounds and the repo route (2026-10-26)

`www/bg/*.jpg` are the six sky photos (1920x1200). This folder is published as the public repo `ty496/ha-dashboard`, and HA pulls files from it with the Downloader integration, which is simpler than the gist for binaries:

```js
const base = 'https://raw.githubusercontent.com/ty496/ha-dashboard/main/';
for (const n of ['dawn','day','cloudy','rain','dusk','night'])
  await h.callService('downloader','download_file',{url: base+'www/bg/'+n+'.jpg', subdir:'www/bg', filename:n+'.jpg', overwrite:true});
await h.callService('downloader','download_file',{url: base+'themes/show_glass.yaml', subdir:'themes', filename:'show_glass.yaml', overwrite:true});
```

Push first (`git push`), then run the snippet. If `/local/bg/<name>.jpg` 404s after the first ever download, restart HA core: `/config/www` must exist at boot for `/local/` to be served.

Known gap: the calendar card paints its inner `.fc` divs with `--ha-card-background`, so translucent glass stacks into a pale panel. Needs card-mod (HACS).
