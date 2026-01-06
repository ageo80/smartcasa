import logging
import aiohttp
import asyncio
from datetime import timedelta
from homeassistant.core import HomeAssistant, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)
DOMAIN = "smartcasa"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    conf = entry.data
    base_url = conf['server_url'].rstrip('/')
    server_url = f"{base_url}/api_bridge.php"
    
    async def send_to_server(payload):
        payload.update({"token": conf.get('token'), "api_key": conf.get('api_key')})
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(server_url, json=payload, timeout=10) as resp:
                    return await resp.json() if resp.status == 200 else None
            except Exception:
                return None

    # Nome funzione esattamente come richiesto dall'errore
    async def sync_all_entities():
        entities = []
        for state in hass.states.async_all():
            if state.domain in ['light', 'cover', 'switch', 'climate']:
                entities.append({
                    "entity_id": state.entity_id,
                    "friendly_name": state.attributes.get('friendly_name', state.entity_id),
                    "state": state.state
                })
        await send_to_server({"action": "sync_entities", "entities": entities})

    async def poll_commands_interval(_now):
        response = await send_to_server({"action": "poll_commands"})
        if response and response.get("status") == "success":
            for cmd in response.get("commands", []):
                domain, service = cmd['service'].split('.')
                data = cmd.get('payload', {}) or {}
                data["entity_id"] = cmd['entity_id']
                await hass.services.async_call(domain, service, data)

    # ESECUZIONE (Riga 45)
    hass.async_create_task(sync_all_entities())
    async_track_time_interval(hass, poll_commands_interval, timedelta(seconds=10))

    async def handle_state_change(event: Event):
        new_state = event.data.get("new_state")
        if new_state and new_state.domain in ['light', 'cover', 'switch', 'climate']:
            await send_to_server({
                "action": "update_state",
                "entity_id": event.data.get("entity_id"),
                "state": new_state.state
            })

    hass.bus.async_listen("state_changed", handle_state_change)
    return True