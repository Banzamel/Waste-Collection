# 🚛 Waste Collection — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/Banzamel/Waste-Collection)](https://github.com/Banzamel/Waste-Collection/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.7%2B-blue.svg)](https://www.home-assistant.io/)

A custom Home Assistant integration for tracking your waste collection schedule. Displays a clean Lovelace card with 5 waste type tiles, countdown timers, and visual urgency alerts — plus sensors ready for use in your own automations and notifications.

---

## ✨ Features

- **5 waste types** — Bio, Mixed, Plastic, Paper, Glass
- **Countdown timers** — each tile shows how many days until the next pickup
- **Visual urgency** — tiles pulse and highlight when collection is today or tomorrow
- **Schedule management** — add and remove dates directly from the card UI
- **ICS import** — import a calendar file from your municipality's website
- **JSON import** — bulk import via a simple JSON file
- **HA services** — add or update pickups programmatically via Home Assistant services
- **Persistent storage** — all data is saved to `.storage/` and survives restarts
- **Automation-ready** — dedicated sensor per waste type for use in notification automations
- **Calendar entity** — pickups appear in the Home Assistant calendar and work with calendar triggers
- **Today / tomorrow binary sensors** — simple on/off entities for automation conditions
- **Next collection sensor** — the nearest pickup date with all waste types collected that day
- **Midnight refresh** — countdowns update automatically every day, no restart needed

---

## 🖼️ Card Preview

> The card adapts to your Home Assistant theme — dark tiles with colored top borders that highlight on urgent days.

```yaml
type: custom:waste-collection-card
```

---

## 📦 Entities Created

All entities are grouped under a single **Waste Collection** device.

### Sensors

| Entity | Description | State |
|--------|-------------|-------|
| `sensor.waste_collection_schedule` | Master sensor with all pickups | Total number of entries |
| `sensor.waste_collection_next` | Nearest collection day | Date (`2026-03-06`) |
| `sensor.waste_collection_bio` | Bio / organic waste | Days until next pickup |
| `sensor.waste_collection_mixed` | Mixed / general waste | Days until next pickup |
| `sensor.waste_collection_plastic` | Plastic & metals | Days until next pickup |
| `sensor.waste_collection_paper` | Paper & cardboard | Days until next pickup |
| `sensor.waste_collection_glass` | Glass | Days until next pickup |

Each waste type sensor exposes `next_date` (ISO date of the next pickup), `waste_type` and `label` attributes.

`sensor.waste_collection_next` exposes:

| Attribute | Example | Description |
|-----------|---------|-------------|
| `days` | `1` | Days until the collection |
| `types` | `["bio", "mixed"]` | Waste types collected that day |
| `labels` | `["Bio", "Mixed"]` | Localized names (English or Polish, following the HA language) |
| `description` | `Bio, Mixed` | Labels joined into one string — handy for notifications |

### Binary sensors

| Entity | On when |
|--------|---------|
| `binary_sensor.waste_collection_today` | Any waste is collected today |
| `binary_sensor.waste_collection_tomorrow` | Any waste is collected tomorrow |
| `binary_sensor.waste_collection_<type>_today` | Given type is collected today (e.g. `binary_sensor.waste_collection_bio_today`) |
| `binary_sensor.waste_collection_<type>_tomorrow` | Given type is collected tomorrow |

`binary_sensor.waste_collection_today` and `_tomorrow` also expose `date`, `types`, `labels` and `description` attributes.

### Calendar

`calendar.waste_collection` contains one all-day event per pickup. It shows up in the **Calendar** panel and can be used with calendar triggers:

```yaml
trigger:
  - platform: calendar
    event: start
    entity_id: calendar.waste_collection
    offset: "-5:00:00"   # 19:00 the evening before
```

All values refresh automatically at midnight (in your Home Assistant time zone).

---

## 📥 Installation

### Via HACS (Recommended)

1. Open **HACS** → **Integrations**
2. Click the three-dot menu (⋮) → **Custom repositories**
3. Add this repository URL and select category **Integration**:
   ```
   https://github.com/Banzamel/Waste-Collection
   ```
4. Find **Waste Collection** in the list and click **Download**
5. Restart Home Assistant
6. Go to **Settings** → **Devices & Services** → **Add Integration**
7. Search for **Waste Collection** and add it

### Manual Installation

1. Download `waste_collection.zip` from the [latest release](https://github.com/Banzamel/Waste-Collection/releases/latest)
2. Unpack it into your Home Assistant `custom_components` directory, so that you get:
   ```
   /config/custom_components/waste_collection/manifest.json
   ```
3. Restart Home Assistant
4. Add the integration via **Settings** → **Devices & Services**

### Updating

- **HACS:** open **HACS** → **Waste Collection** → **Update** (or ⋮ → **Redownload** and pick a version), then restart Home Assistant.
- **Manual:** delete `/config/custom_components/waste_collection/`, unpack the new `waste_collection.zip` in its place and restart Home Assistant.

Your schedule is kept in `.storage/waste_collection.storage`, so updating or reinstalling the integration does not remove it. After an update, refresh the browser with `Ctrl + Shift + R` so the new card version is loaded.

---

## 🎴 Adding the Card

After installation the Lovelace card is registered automatically. Add it to any dashboard:

**Via UI:** Edit dashboard → Add Card → search for *Waste Collection*

**Via YAML:**
```yaml
type: custom:waste-collection-card
```

---

## 📅 Managing Your Schedule

There are four ways to enter pickup dates:

### Method 1 — Card UI (manual)

Click the 📅 icon in the top-right corner of the card. Select the waste type, pick a date, and click **Add**. Repeat for each pickup. Use ✕ to remove individual entries.

### Method 2 — ICS Import (recommended)

Many municipalities publish waste collection calendars as `.ics` (iCal) files. Download the file and import it via the 📥 button on the card.

The integration auto-detects waste types from the event summary. The event name should contain one of these keywords:

| Keyword (any language) | Detected type |
|------------------------|---------------|
| `bio`, `organic`, `green` | `bio` |
| `plastic`, `pet`, `yellow` | `plastic` |
| `paper`, `cardboard`, `blue` | `paper` |
| `glass` | `glass` |
| `mixed`, `general`, `grey`, `gray` | `mixed` |

### Method 3 — JSON Import

Create a `.json` file and import it via the 📥 button. Accepted formats:

```json
{
  "pickups": [
    { "type": "bio",     "date": "2026-03-06" },
    { "type": "mixed",   "date": "2026-03-06" },
    { "type": "plastic", "date": "2026-03-13" },
    { "type": "paper",   "date": "2026-03-13" },
    { "type": "glass",   "date": "2026-03-27" }
  ]
}
```

Valid `type` values: `bio` · `mixed` · `plastic` · `paper` · `glass`. Entries with an unknown type or an invalid date, as well as duplicates, are skipped.

An array format is also accepted:
```json
[
  { "type": "bio", "date": "2026-03-06" },
  { "type": "mixed", "date": "2026-03-06" }
]
```

A ready-made example file for the full year 2026 (`custom_components/waste_collection/example_collection_date.json`) is included in this repository.

### Method 4 — Home Assistant Services

#### Add a single pickup
```yaml
service: waste_collection.add_pickup
data:
  type: bio
  date: "2026-03-06"
```

#### Replace the entire schedule
```yaml
service: waste_collection.update_schedule
data:
  pickups:
    - type: bio
      date: "2026-03-06"
    - type: mixed
      date: "2026-03-06"
    - type: plastic
      date: "2026-03-13"
```

#### Remove a single pickup
```yaml
service: waste_collection.remove_pickup
data:
  type: glass
  date: "2026-03-27"
```

---

## 🔔 Notification Automations

Below is a ready-to-use example that sends a push notification at 7 PM whenever any collection is happening the next day:

```yaml
automation:
  alias: "Waste Collection Reminder"
  trigger:
    - platform: time
      at: "19:00:00"
  condition:
    - condition: state
      entity_id: binary_sensor.waste_collection_tomorrow
      state: "on"
  action:
    - service: notify.mobile_app_your_phone
      data:
        title: "🚛 Waste collection reminder"
        message: >
          Put out: {{ state_attr('binary_sensor.waste_collection_tomorrow', 'description') }}
```

Replace `notify.mobile_app_your_phone` with your actual notification service.

Need a reminder for one type only? Use e.g. `binary_sensor.waste_collection_glass_tomorrow` in the condition.

---

## 🔧 Technical Details

### File Structure

```
custom_components/waste_collection/
├── __init__.py            # Integration setup, services, midnight refresh, card registration
├── binary_sensor.py       # Today / tomorrow binary sensors
├── calendar.py            # Calendar entity
├── config_flow.py         # UI configuration flow
├── const.py               # Constants and waste type labels
├── entity.py              # Shared base entity (device info, update signal)
├── manifest.json          # Integration metadata
├── schedule.py            # Schedule storage and queries
├── sensor.py              # Sensor entities
├── services.yaml          # Service definitions
├── brand/
│   ├── icon.png           # Integration icon (256×256)
│   └── icon@2x.png        # Integration icon (512×512)
├── translations/
│   ├── en.json            # English translations
│   └── pl.json            # Polish translations
└── www/
    └── waste-card.js      # Custom Lovelace card
```

### Storage

- Data is stored in: `.storage/waste_collection.storage`
- Automatically saved on every change
- Survives restarts and updates

### Available Services

| Service | Description |
|---------|-------------|
| `waste_collection.update_schedule` | Replace entire pickup list |
| `waste_collection.add_pickup` | Add a single pickup entry |
| `waste_collection.remove_pickup` | Remove a specific pickup entry |

---

## 🐛 Troubleshooting

**Card doesn't appear after installation**
Clear your browser cache with `Ctrl + Shift + R` and restart Home Assistant. Check the browser console (F12) for JavaScript errors.

**ICS import doesn't detect waste types**
Make sure the event names in your calendar file contain recognizable keywords (`bio`, `plastic`, `paper`, `glass`, `mixed`). Open the `.ics` file in a text editor to check the `SUMMARY:` fields.

**Sensors show `unknown` state**
This means no future pickups are scheduled for that waste type. Add dates via the card or import a schedule file.

**Data lost after restart**
Check Home Assistant logs for storage write errors. Verify that the `.storage/` directory is writable.

---

## 🤝 Contributing

Contributions are welcome! To get started:

```bash
git clone https://github.com/Banzamel/Waste-Collection.git
cd Waste-Collection

# Symlink to your HA config for live development
ln -s $(pwd)/custom_components/waste_collection /path/to/homeassistant/custom_components/waste_collection
```

Please open an issue before submitting large changes.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- 🐛 **Bug reports & feature requests** → [GitHub Issues](https://github.com/Banzamel/Waste-Collection/issues)
- 💬 **Discussions** → [GitHub Discussions](https://github.com/Banzamel/Waste-Collection/discussions)
- ⭐ **Like the project?** Give it a star!

---

*This integration is a community project and is not affiliated with or endorsed by Home Assistant or Nabu Casa.*
