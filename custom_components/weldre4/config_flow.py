import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_PERSON_ID


class WeldRe4ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Weld RE-4."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            # Optionally validate user inputs here
            return self.async_create_entry(title="Weld RE-4", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_PERSON_ID): str,
                }
            ),
            errors=errors,
        )
