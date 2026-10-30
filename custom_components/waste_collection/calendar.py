from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import WasteCollectionEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup calendar from config entry."""
    async_add_entities([WasteCollectionCalendar(entry)])


class WasteCollectionCalendar(WasteCollectionEntity, CalendarEntity):
    """Calendar with one all-day event per pickup."""

    _attr_name = None  # use the device name: "Waste Collection"
    _attr_unique_id = "waste_collection_calendar"
    _attr_icon = "mdi:calendar-blank-multiple"

    def __init__(self, entry: ConfigEntry):
        super().__init__(entry, "calendar.waste_collection")

    def _event(self, pickup_date: date, waste_type: str) -> CalendarEvent:
        return CalendarEvent(
            start=pickup_date,
            end=pickup_date + timedelta(days=1),
            summary=self._schedule.label(waste_type),
            uid=f"{waste_type}_{pickup_date.isoformat()}",
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Current or next upcoming event."""
        today = self._schedule.today()
        for pickup_date, waste_type in self._schedule.dated_pickups():
            if pickup_date >= today:
                return self._event(pickup_date, waste_type)
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        events = []
        for pickup_date, waste_type in self._schedule.dated_pickups():
            event_start = dt_util.start_of_local_day(pickup_date)
            event_end = dt_util.start_of_local_day(pickup_date + timedelta(days=1))
            if event_start < end_date and event_end > start_date:
                events.append(self._event(pickup_date, waste_type))
        return events
