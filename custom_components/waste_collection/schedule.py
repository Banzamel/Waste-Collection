import logging
from dataclasses import dataclass
from datetime import date

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import SIGNAL_SCHEDULE_UPDATED, WASTE_TYPES, waste_label

_LOGGER = logging.getLogger(__name__)


def _parse_date(value) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def normalize_pickups(pickups) -> list[dict]:
    """Drop invalid entries and duplicates, return list sorted by date and type."""
    seen = set()
    result = []
    for pickup in pickups or []:
        if not isinstance(pickup, dict):
            _LOGGER.warning("Ignoring invalid pickup entry: %s", pickup)
            continue
        waste_type = pickup.get("type")
        pickup_date = _parse_date(pickup.get("date"))
        if waste_type not in WASTE_TYPES or pickup_date is None:
            _LOGGER.warning("Ignoring invalid pickup entry: %s", pickup)
            continue
        key = (waste_type, pickup_date)
        if key in seen:
            continue
        seen.add(key)
        result.append({"type": waste_type, "date": pickup_date.isoformat()})
    result.sort(key=lambda p: (p["date"], WASTE_TYPES.index(p["type"])))
    return result


class WasteSchedule:
    """Holds the pickup list, persists it and notifies entities about changes."""

    def __init__(self, hass: HomeAssistant, store: Store, pickups: list[dict]):
        self.hass = hass
        self._store = store
        self._pickups = normalize_pickups(pickups)

    @classmethod
    async def async_load(cls, hass: HomeAssistant, store: Store) -> "WasteSchedule":
        stored_data = await store.async_load()
        pickups = stored_data.get("pickups", []) if stored_data else []
        return cls(hass, store, pickups)

    @property
    def pickups(self) -> list[dict]:
        return self._pickups

    @property
    def language(self) -> str:
        return self.hass.config.language

    def label(self, waste_type: str) -> str:
        return waste_label(self.language, waste_type)

    @staticmethod
    def today() -> date:
        """Current date in Home Assistant's configured time zone."""
        return dt_util.now().date()

    def dated_pickups(self):
        """Yield (date, type) tuples for all pickups."""
        for pickup in self._pickups:
            yield date.fromisoformat(pickup["date"]), pickup["type"]

    def next_pickup(self, waste_type: str) -> date | None:
        today = self.today()
        for pickup_date, pickup_type in self.dated_pickups():
            if pickup_type == waste_type and pickup_date >= today:
                return pickup_date
        return None

    def types_on(self, day: date) -> list[str]:
        return [t for d, t in self.dated_pickups() if d == day]

    def next_collection(self) -> tuple[date, list[str]] | None:
        """Return the nearest pickup day (today included) with all its waste types."""
        today = self.today()
        for pickup_date, _ in self.dated_pickups():
            if pickup_date >= today:
                return pickup_date, self.types_on(pickup_date)
        return None

    async def async_set_pickups(self, pickups) -> None:
        self._pickups = normalize_pickups(pickups)
        await self._async_save()

    async def async_add_pickup(self, waste_type: str, pickup_date: date) -> None:
        await self.async_set_pickups(
            self._pickups + [{"type": waste_type, "date": pickup_date.isoformat()}]
        )

    async def async_remove_pickup(self, waste_type: str, pickup_date: date) -> None:
        date_str = pickup_date.isoformat()
        await self.async_set_pickups(
            [p for p in self._pickups if not (p["type"] == waste_type and p["date"] == date_str)]
        )

    async def _async_save(self) -> None:
        await self._store.async_save({"pickups": self._pickups})
        self.async_notify()

    def async_notify(self) -> None:
        """Ask all entities to refresh their state."""
        async_dispatcher_send(self.hass, SIGNAL_SCHEDULE_UPDATED)


@dataclass
class WasteCollectionData:
    """Runtime data stored on the config entry."""

    schedule: WasteSchedule
    version: str
