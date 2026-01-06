import logging
import aiohttp
import asyncio
import json
from datetime import timedelta
from homeassistant.core import HomeAssistant, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)
DOMAIN = "smartcasa"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    conf = entry.data
    server_url = f"{conf['server_url'].rstrip('/')}/api_bridge.php"
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"whitelist": []}

    async def send_to_server(payload):
        payload.update({"token": conf.get('token'), "api_key": conf.get('api_key')})
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(server_url, json=payload, timeout=10) as resp:
                    return await resp.json() if resp.status == 200 else None
            except Exception as e:
                _LOGGER.error("Errore SmartCasa: %s", e)
                return None

    async def sync_all_entities():
        entities = []
        for state in hass.states.async_all():
            # Supporto universale per ogni dominio
            entities.append({
                "entity_id": state.entity_id,
                "friendly_name": state.attributes.get('friendly_name', state.entity_id),
                "state": state.state,
                "unit": state.attributes.get('unit_of_measurement', ''),
                "attributes": dict(state.attributes)
            })
        
        response = await send_to_server({"action": "sync_entities", "entities": entities})
        if response and "allowed_entities" in response:
            hass.data[DOMAIN][entry.entry_id]["whitelist"] = response["allowed_entities"]

    async def poll_commands_interval(_now):
        response = await send_to_server({"action": "poll_commands"})
        if response and response.get("status") == "success":
            for cmd in response.get("commands", []):
                domain, service = cmd['service'].split('.')
                data = cmd.get('payload', {}) or {}
                data["entity_id"] = cmd['entity_id']
                await hass.services.async_call(domain, service, data)

    # Avvio Task
    hass.async_create_task(sync_all_entities())
    async_track_time_interval(hass, poll_commands_interval, timedelta(seconds=10))

    async def handle_state_change(event: Event):
        new_state = event.data.get("new_state")
        if not new_state: return
        
        entity_id = event.data.get("entity_id")
        if entity_id in hass.data[DOMAIN][entry.entry_id].get("whitelist", []):
            await send_to_server({
                "action": "update_state",
                "entity_id": entity_id,
                "state": new_state.state,
                "attributes": dict(new_state.attributes)
            })

    hass.bus.async_listen("state_changed", handle_state_change)
    return Trueimport logging
import aiohttp
import asyncio
import json
from datetime import timedelta
from homeassistant.core import HomeAssistant, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)
DOMAIN = "smartcasa"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    conf = entry.data
    server_url = f"{conf['server_url'].rstrip('/')}/api_bridge.php"
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"whitelist": []}

    async def send_to_server(payload):
        payload.update({"token": conf.get('token'), "api_key": conf.get('api_key')})
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(server_url, json=payload, timeout=10) as resp:
                    return await resp.json() if resp.status == 200 else None
            except Exception as e:
                _LOGGER.error("Errore SmartCasa: %s", e)
                return None

    async def sync_all_entities():
        entities = []
        for state in hass.states.async_all():
            # Supporto universale per ogni dominio
            entities.append({
                "entity_id": state.entity_id,
                "friendly_name": state.attributes.get('friendly_name', state.entity_id),
                "state": state.state,
                "unit": state.attributes.get('unit_of_measurement', ''),
                "attributes": dict(state.attributes)
            })
        
        response = await send_to_server({"action": "sync_entities", "entities": entities})
        if response and "allowed_entities" in response:
            hass.data[DOMAIN][entry.entry_id]["whitelist"] = response["allowed_entities"]

    async def poll_commands_interval(_now):
        response = await send_to_server({"action": "poll_commands"})
        if response and response.get("status") == "success":
            for cmd in response.get("commands", []):
                domain, service = cmd['service'].split('.')
                data = cmd.get('payload', {}) or {}
                data["entity_id"] = cmd['entity_id']
                await hass.services.async_call(domain, service, data)

    # Avvio Task
    hass.async_create_task(sync_all_entities())
    async_track_time_interval(hass, poll_commands_interval, timedelta(seconds=10))

    async def handle_state_change(event: Event):
        new_state = event.data.get("new_state")
        if not new_state: return
        
        entity_id = event.data.get("entity_id")
        if entity_id in hass.data[DOMAIN][entry.entry_id].get("whitelist", []):
            await send_to_server({
                "action": "update_state",
                "entity_id": entity_id,
                "state": new_state.state,
                "attributes": dict(new_state.attributes)
            })

    hass.bus.async_listen("state_changed", handle_state_change)
    return True