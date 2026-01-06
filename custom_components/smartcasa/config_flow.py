import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

DOMAIN = "smartcasa"

class SmartCasaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce la configurazione iniziale via UI."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Qui potresti aggiungere un test di connessione al tuo api_bridge.php
            return self.async_create_entry(title=user_input["nome_casa"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("nome_casa", default="Casa Mia"): str,
                vol.Required("server_url", default="https://tuosito.it"): str,
                vol.Required("token"): str,
                vol.Required("api_key"): str,
            }),
            errors=errors,
        )