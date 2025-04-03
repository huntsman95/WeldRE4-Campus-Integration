from homeassistant.helpers.entity import Entity
from .const import DOMAIN, CONF_PERSON_ID


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data[
        "coordinator"
    ]  # Access coordinator from stored runtime data

    person_id = entry.data[CONF_PERSON_ID]  # Retrieve Person ID from config

    async_add_entities(
        [
            WeldRe4AssignmentsSensor(coordinator, entry, person_id),
            WeldRe4MissingAssignmentsSensor(coordinator, entry, person_id),
        ],
        update_before_add=True,
    )


class WeldRe4AssignmentsSensor(Entity):
    """Sensor representing the total assignment count."""

    def __init__(self, coordinator, entry, person_id):
        self._coordinator = coordinator
        self._entry = entry
        self._person_id = person_id  # Store Person ID

    @property
    def name(self):
        # Include the Person ID in the sensor name
        return f"Weld RE-4 {self._person_id} Total Assignments"

    @property
    def state(self):
        # Return the total number of items in the JSON array
        if self._coordinator.data:
            return len(self._coordinator.data)
        return None

    @property
    def should_poll(self):
        return True

    @property
    def unique_id(self):
        # Generate a unique ID based on the config entry ID
        return f"{self._entry.entry_id}_assignments_sensor"

    async def async_update(self):
        # Use the coordinator to refresh data
        await self._coordinator.async_request_refresh()


class WeldRe4MissingAssignmentsSensor(Entity):
    """Sensor representing the missing assignment count."""

    def __init__(self, coordinator, entry, person_id):
        self._coordinator = coordinator
        self._entry = entry
        self._person_id = person_id  # Store Person ID

    @property
    def name(self):
        # Include the Person ID in the sensor name
        return f"Weld RE-4 {self._person_id} Missing Assignments"

    @property
    def state(self):
        # Count the entries with "missing" set to True
        if self._coordinator.data:
            return sum(
                1 for item in self._coordinator.data if item.get("missing") is True
            )
        return None

    @property
    def should_poll(self):
        return True

    @property
    def unique_id(self):
        # Generate a unique ID based on the config entry ID and Person ID
        return f"{self._entry.entry_id}_missing_assignments_sensor"

    async def async_update(self):
        # Use the coordinator to refresh data
        await self._coordinator.async_request_refresh()
