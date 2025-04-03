from datetime import timedelta
import logging
import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_PERSON_ID, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Weld RE-4 integration."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # Create runtime storage for this entry
    hass.data[DOMAIN][entry.entry_id] = {
        "session": aiohttp.ClientSession(),
        "authenticated": False,
    }

    async def authenticate():
        """Authenticate to the API and retain session state."""
        session = hass.data[DOMAIN][entry.entry_id]["session"]
        url = "https://weldre4co.infinitecampus.org/campus/verify.jsp"
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Origin": "https://weldre4co.infinitecampus.org",
            "DNT": "1",
            "Referer": "https://weldre4co.infinitecampus.org/campus/portal/parents/weldre4.jsp",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Priority": "u=0, i",
            "TE": "trailers",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        }
        payload = {
            "username": entry.data[CONF_USERNAME],
            "password": entry.data[CONF_PASSWORD],
            "portalUrl": "portal/parents/weldre4.jsp?&rID=0.8343994099932464",
            "appName": "weldre4",
            "url": "nav-wrapper",
            "lang": "en",
            "portalLoginPage": "parents",
        }

        async with session.post(url, headers=headers, data=payload) as response:
            if response.status == 200:
                hass.data[DOMAIN][entry.entry_id]["authenticated"] = True
                _LOGGER.info("Authentication successful")
            else:
                hass.data[DOMAIN][entry.entry_id]["authenticated"] = False
                _LOGGER.error("Authentication failed")
                raise UpdateFailed("Failed to authenticate")

    async def fetch_assignments():
        """Fetch assignments data using the persistent session."""
        session = hass.data[DOMAIN][entry.entry_id]["session"]
        url = f"https://weldre4co.infinitecampus.org/campus/api/portal/assignment/listView?personID={entry.data[CONF_PERSON_ID]}"

        if not hass.data[DOMAIN][entry.entry_id]["authenticated"]:
            await authenticate()

        async with session.get(url) as response:
            if response.status == 403:
                _LOGGER.warning("403 Forbidden. Reauthenticating...")
                await authenticate()
                return await fetch_assignments()  # Retry after reauthentication
            elif response.status == 200:
                return await response.json()
            else:
                _LOGGER.error("Unexpected response: %s", response.status)
                raise UpdateFailed(f"Unexpected HTTP status: {response.status}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Weld RE-4 Data",
        update_method=fetch_assignments,
        update_interval=SCAN_INTERVAL,
    )

    # Store coordinator for reference
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    await coordinator.async_config_entry_first_refresh()

    # Corrected: Await the coroutine
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if entry_data and "session" in entry_data:
        await entry_data["session"].close()  # Properly close the session

    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
