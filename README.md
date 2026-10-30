# ha-dashboard

Home Assistant wall dashboard for the Echo Show 8 (2nd gen, 1280x800).

- `show.json` is the source of truth (pretty-printed). `show.min.json` is the same thing minified for pasting.
- Live copy: HA storage dashboard `/dashboard-show` ("Show"). Views: `home` plus subviews `living-room`, `family-room`, `kitchen`, `basement`, `primary`, `outside`.
- HACS cards in use: Kiosk Mode (open `/dashboard-show/home?kiosk` on the Show), card-mod, mini-media-player, Atomic Calendar Revive (the home-screen calendar, agenda mode), Team Tracker integration + card (`sensor.broncos`, NFL). Everything else is native HA 2026.10.

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

Everything comes through the Hubitat integration (Maker API 144) except: `sensor.sunrise_time` and `sensor.sunset_time` (Template helpers, `%-I:%M %p` of sun.sun next_rising/next_setting), `sensor.moon_phase` (Moon integration), `weather.forecast_home` (met.no), the calendars (`calendar.home`, `calendar.olive`, `calendar.travel` are iCloud via the CalDAV integration, signed in with Ty's Apple ID and an app-specific password; `calendar.birthdays` and `calendar.ty_mercer90_gmail_com` are Google Calendar), `todo.shopping_list`, `media_player.family_room_family_room_wiim` (WiiM), `media_player.family_room_family_room_homepod` (Apple TV integration), `media_player.basement_receiver` (Denon), `media_player.shield` and `media_player.65q750g` (Cast). If an entity id changes in HA, search this file for the old id.

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

### Comic-strip set and the glass recipe (2026-10-27)

Backgrounds are now the seven comic-strip beagle scenes `www/bg/strip-{dawn,day,cloudy,rain,dusk,night,halloween}.jpg` (Nano Banana, all edited from one base render so the street stays put). The alpine photos remain in `www/bg` unused. `Glass Halloween` takes the night slot from Oct 24 to 31 (template in the automation checks `now().month == 10 and now().day >= 24`).

Glass recipe lives in `glass()` at the top of `build_glass.js`: `blur(14px) saturate(150%)`, fill 0.12 (dark) / 0.34 (light) white, 1px border, and the box-shadow stack `inset 0 1px 0` (top hairline), `inset 0 -1px 0` (bottom rim), `inset 0 -10px 18px -14px` (bottom specular glow), plus the drop shadow. Tune those four numbers, rebuild, push, re-download, `frontend.reload_themes`.

### Phones (2026-10-27)

Backgrounds are `center calc(50vh - 31.25vw) / 100% auto` with the scene's sky colour (sampled from the image's top edge) as the final layer. The image is 1.6:1 and 100vw wide, so that offset centres it in the first screen; on the 16:10 Show it is 0, i.e. plain `cover`. HA's view background is `position: absolute` inside the scrolling view, so on a phone the scene starts centred and scrolls away with the cards (1:1; real parallax would need card-mod on hui-root).

Gotcha: `raw.githubusercontent.com` caches for 5 minutes per edge, and HA's edge can lag yours. When a re-download brings back the old file, use the commit URL instead: `https://raw.githubusercontent.com/ty496/ha-dashboard/<sha>/themes/show_glass.yaml`.

### Sky tiles (2026-10-27)

On a phone the scene sits at the bottom of the scrolling view and the sky colour fills the rest, so transparent tiles repeat above it: `www/bg/stars.png` (night, Halloween), `stars-dusk.png` (dusk), `rain.png` (rain). Drawn by `www/bg/make_tiles.ps1` in the strip's flat style; day skies stay plain. The tile layer sits under the image in the `lovelace-background` stack, so it never shows on the Show where the image covers the screen.

### Holiday schedule (2026-10-27)

Three more scenes and themes: `strip-thanksgiving.jpg` (Glass Thanksgiving, light), `strip-christmas.jpg` (Glass Christmas, dark, snow tile) and `strip-christmas-day.jpg` (Glass Christmas Day, light, snow tile; the first cast render, Ty's pick). The automation template decides, in this order:

1. Night (elevation < -6): Halloween Oct 24-31, Christmas all of December, otherwise Night.
2. Dec 25 daytime: Christmas Day.
3. Thanksgiving week daytime (Monday to Sunday around the 4th Thursday; `tg = 22 + ((3 - nov1.weekday()) % 7)`): Thanksgiving.
4. Otherwise Dawn/Dusk/Rain/Cloudy/Day as before.

Dry-run any date with HA's `render_template` by substituting `now()` with `as_datetime('YYYY-MM-DD HH:MM:SS')` and the elevation with a number; that was done for 2026 and the windows check out.

## Planes overhead (2026-10-30)

An "Overhead now" glass card at the top of the home view's right column, plus a full-screen poster
(FlightPortrait style, red print, serif captions) for 20 s when a plane enters the area.

- **Data:** Flightradar24 custom integration (HACS, AlexandrErohin), 8 km around `zone.home`, 30 s polling.
  `sensor.flightradar24_current_in_area` carries a `flights` list; `flightradar24_entry` fires per new plane.
- **Art:** `www/planes/<airline ICAO>-<type ICAO>.webp` (31 combos) and `GEN-*.webp` (12 white fallbacks),
  served from `/config/www/planes` at `/local/planes`. Made in `planes/` (Nano Banana from Commons photos,
  keyed off magenta by `planes/cutout.py`); the 2K masters stay local.
- **Lookup:** `custom_templates/planes.jinja` (macros `plane_key`, `plane_art`, `plane_where`, ...) maps a flight to
  its drawing: exact combo, then the airline's nearest sibling type, then a GEN class. SkyWest/Republic and other
  regionals map to United Express (`UAX`). Test it locally with a plain jinja2 stub before shipping.
- **Cards:** inserted by `scripts/planes-cards.js` (idempotent). The poster is a markdown card made
  `position: fixed` by card-mod; it shows while `input_boolean.plane_takeover` is on.
- **Automations:** `automations/planes_overhead_takeover.json` (07:00-22:00, airborne only, at most every
  15 min, sets `input_text.plane_takeover_id`) and `automations/planes_overhead_count.json` (`counter.planes_today`,
  reset at midnight, shown in the poster footer).
- **Install:** paste `planes/deploy_ha.js` into a signed-in admin HA tab, then `await planesPhase1()`,
  `await planesRestart()`, reload, `await planesPhase2()`. `await planesTestTakeover()` previews the poster.
