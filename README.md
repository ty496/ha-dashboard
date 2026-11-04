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
- **Art:** `www/planes/<airline ICAO>-<type ICAO>.webp` (31 combos), `GEN-*.webp` (12 white fallbacks) and `MIL-H47.webp` (Army CH-47F Chinook, added 2026-11-03),
  served from `/config/www/planes` at `/local/planes`. Made in `planes/` (Nano Banana from Commons photos,
  keyed off magenta by `planes/cutout.py`); the 2K masters stay local.
- **Lookup:** `custom_templates/planes.jinja` (macros `plane_key`, `plane_art`, `plane_where`, ...) maps a flight to
  its drawing: exact combo, then the airline's nearest sibling type, then a GEN class. SkyWest/Republic and other
  regionals map to United Express (`UAX`). Test it locally with a plain jinja2 stub before shipping.
- **Cards:** inserted by `scripts/planes-cards.js` (idempotent). The poster is a markdown card made
  `position: fixed` by card-mod; it shows while `input_boolean.plane_takeover` is on.
- **Live map:** tapping the card's drawing opens the `#plane` Bubble Card pop-up, which holds the integration's own
  `custom:flightradar24-card` (Leaflet map of the area, every flight with its trail; loaded from `/flightradar24/`).
- **Automations:** `automations/planes_overhead_takeover.json` (07:00-22:00, airborne only; picks the planes
  that get the poster) calls `ha-scripts/plane_poster.json` (`script.plane_poster`: at most every 5 min, sets
  `input_text.plane_takeover_id`), and `automations/planes_overhead_count.json` (`counter.planes_today`, reset at
  midnight, shown in the poster footer).
- **Flight-school filter (2026-11-03):** `plane_boring(f)` in `planes.jinja` marks a light piston plane (the
  GEN-C172, GEN-P28A, GEN-SR22 and GEN-PA44 classes, which include unknown private types) with no destination:
  the C172s and Archers circling on VFR all day. Those don't get a poster or a place in `counter.planes_today`,
  and `plane_pick` skips them for the card. The card shows while `sensor.planes_worth_showing` (a template helper:
  `{% from 'planes.jinja' import plane_count %}{{ plane_count() | trim }}`) is above 0. Anything with a
  destination, helicopters (the Chinooks have none) and everything bigger still shows. The Live map shows all.
- **Poster only for some planes (2026-11-04):** Denver departures brought the poster up every 9 minutes, so it now goes
  to the first plane of each kind a day (airline and type, `UAL-B738`; `PVT-<type>` for private aircraft) and to
  unusual ones: helicopters, wide-bodies, people of interest and private jets with a registered owner (the last two
  wait up to 40 s for `sensor.plane_details` to pair the flight). Kinds that had a poster go in the local to-do list
  `todo.plane_posters_today` (not exposed to Assist), which `planes_overhead_count` clears at midnight. Every plane
  worth showing is still on the card.
- **Install:** paste `planes/deploy_ha.js` into a signed-in admin HA tab, then `await planesPhase1()`,
  `await planesRestart()`, reload, `await planesPhase2()`. `await planesTestTakeover()` previews the poster.
- **Plane details (2026-11-03):** `custom_components/plane_details`, a second source. Flightradar24 honours the
  FAA's LADD list, so private aircraft whose owners asked arrive as callsign "Blocked" with no registration.
  Every 30 s the integration polls adsb.lol (unfiltered ADS-B, free, no key) for 6 nm round home, pairs its
  aircraft with Flightradar24's flights (registration, callsign, else nearest of the same type within 15 km),
  and adds the registered owner (adsbdb, cached a month, 6 lookups a poll) and plane-alert-db's entry for
  notable aircraft (read once a day). People of interest are its categories Climate Crisis (celebrities' and
  billionaires' jets), Don't you know who I am?, As Seen on TV (more celebrities, and news helicopters), Joe Cool,
  Big Hello, Dictator Alert and Governments; the name
  shown is the operator, or the first tag that reads like a person when the operator is a company (Elon Musk,
  not Falcon Landing LLC). `sensor.plane_details` holds `by_fr24` (keyed by Flightradar24's flight id),
  `aircraft` and `notable`; `plane_details_notable` fires when a person of interest's aircraft enters the area.
  `plane_extra(f)` in `planes.jinja` returns a flight's record as JSON. The card adds "★ name category" and
  "Owned by ..." (private aircraft), both cards use the unblocked registration, and `plane_boring` never hides a
  person of interest. PIA aircraft (the FAA's anonymous addresses) can't be named by anyone. Install: Downloader
  the folder into `/config/custom_components/plane_details`, restart, add "Plane details" (one confirm step).

## Voice: Claude can add, change and delete calendar events (2026-11-03)

Home Assistant's CalDAV (iCloud) calendars can only create events, so `custom_components/caldav_edit` adds
`caldav_edit.update_event` and `caldav_edit.delete_event`. They reuse each calendar entity's own CalDAV connection
(no second login) and find an event by title and day across the calendars given. Copies with the same UID are
changed together; ambiguous matches and repeating events are refused with a message the voice assistant can read out.
Timed changes are written in UTC. The logic is in `events.py` (no Home Assistant imports, tested on its own).

Install: Downloader the files into `/config/custom_components/caldav_edit`, restart, then add the "CalDAV edit"
integration (one confirm step). The voice tools are the scripts `add_calendar_event`, `change_calendar_event` and
`delete_calendar_event` (exposed to Assist); "Home" means the shared iCloud Home calendar (`calendar.home_2`).

## Voice: read-only house wiki for Claude (2026-11-03)

`custom_components/house_wiki` gives the voice agent read-only access to household notes kept in a private GitHub
repo (an Obsidian vault). Setup takes a fine-grained token limited to that repo with Contents: Read-only; the entry's
options decide which pages are in scope (included folders, folders whose pages count only when they mention given
terms, excluded paths), so nothing personal lives in this public code. Pages refresh from GitHub every 30 minutes,
fetching only changed files. It registers an LLM API, "House wiki" (`house_wiki`), with two read-only tools,
`search_house_wiki` and `read_house_wiki_page`; select it next to Assist in the conversation agent's settings.
Scope and search are in `wiki.py` (no Home Assistant imports).

## Voice: weather anywhere (2026-11-03)

Weather sites fill in their numbers with scripts, so the agent's web search and fetch only see stale copies.
`custom_components/place_weather` registers the LLM API "Weather anywhere" (`place_weather`) with one read-only tool,
`get_place_weather`: a place name (or latitude/longitude for ski areas and trailheads) goes to Open-Meteo's geocoder
and forecast API (free, no key) and comes back as current conditions, the next 12 hours and up to 7 days, in °F, mph
and inches. Ambiguous names prefer matches within 350 miles of home ("Vail" is Colorado); "Vail, AZ" or
"Paris, France" picks by the qualifier. Matching and shaping are in `openmeteo.py` (no Home Assistant imports).

Since 0.2.0 each answer also goes to a weather entity, `weather.place_weather` (`weather.py`), which takes the
place's short name ("Vail, Colorado", "Paris, France") and its current conditions, 24 hourly and 7 daily forecasts,
so a weather-forecast card draws it like the home forecast. Hours keep their true instant (shown on the home's clock);
days sit at noon of their own date in the home's time zone, so far-east places keep the right weekday. The tool then
fires `place_weather_shown` with `place` and the asking `device_id`. The entity is empty until the first lookup and
after a restart, and is not exposed to Assist.

## Voice: home weather answered locally, with a pop-up (2026-11-03)

- **Answer:** `automations/voice_weather_local.json`. Conversation (sentence) triggers for home weather
  ("what's the weather today", "how's it outside", "will it rain tomorrow", ...) answer from
  `weather.forecast_home` with `set_conversation_response`. Sentence triggers run before the voice
  pipeline's agent, so these never wait on Claude (9 ms through the pipeline, against 3-5 s). Weather for
  another place has no trigger and still goes to Claude's `get_place_weather`. "What's the temperature"
  alone is left to Claude on purpose, since it may mean inside.
- **Pop-up:** `scripts/weather-popup.js` adds a Bubble Card pop-up (`#weather`) to the home view: the
  hourly forecast with current conditions over the week's daily forecast. It opens when
  `input_boolean.kitchen_weather_popup` turns on, which the answer does only when the question came from
  the Kitchen Echo (`trigger.device_id`), and `trigger_close` shuts it when the helper turns off:
  `automations/kitchen_weather_popup_close.json` does that after 30 s, and closing it by hand does too
  (`close_action`). The helper is not exposed to Assist.
- **Other places:** the same pop-up as `#place-weather`, on `weather.place_weather` (see "weather anywhere"
  above). `automations/kitchen_place_weather_popup_open.json` turns on `input_boolean.kitchen_place_weather_popup`
  on `place_weather_shown` from the Kitchen Echo, closing the home pop-up first (and the home answer closes
  this one). The close automation handles both helpers.
- **The Echo's own forecast page:** TECHO5 opens it after any weather question once the answer ends, over
  the dashboard, with no setting or Home Assistant action to stop it (firmware `display.go`: only a tap or
  "go home" clears it). So it wears the dashboard's colors instead: TECHO5 custom themes set on the device's
  setup page (Screen & Photos, Custom colors). Light: ground `#96d3f0` (Glass Day's sky), accent `#2e7d32`,
  text `#1b2230`, dim `#4a5568`, rules `#78bde3`. Dark: ground `#132e48` (Glass Night's sky), accent
  `#6ee7b7`, text `#f2f4f8`, dim `#b4bccb`, rules `#24466a`. The accent is also the colour of the listening
  light. `show_glass_follows_the_sky` now sets `select.kitchen_theme_mode` to Dark with the dark glass themes
  and Light otherwise, only when it changes.
