import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)
DOMAIN = "smartcasa"

# Domini che l'integrazione è in grado di gestire
SUPPORTED_DOMAINS = ['light', 'cover', 'switch', 'climate', 'sensor', 'binary_sensor']

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configurazione dell'integrazione tramite UI."""
    conf = entry.data
    base_url = conf['server_url'].rstrip('/')
    server_url = f"{base_url}/api_bridge.php"
    
    # Memoria locale dell'integrazione
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "whitelist": [],  # Entità autorizzate dal server PHP
        "last_sync": None
    }

    async def send_to_server(payload):
        """Metodo centralizzato per le chiamate API verso il server PHP."""
        payload.update({
            "token": conf.get('token'), 
            "api_key": conf.get('api_key')
        })
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(server_url, json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    _LOGGER.error("Errore server PHP: %s", resp.status)
            except Exception as e:
                _LOGGER.error("Errore connessione SmartCasa: %s", e)
        return None

    async def sync_all_entities():
        """Sincronizza tutte le entità e riceve la whitelist dal server."""
        entities = []
        for state in hass.states.async_all():
            if state.domain in SUPPORTED_DOMAINS:
                entities.append({
                    "entity_id": state.entity_id,
                    "friendly_name": state.attributes.get('friendly_name', state.entity_id),
                    "state": state.state,
                    "unit": state.attributes.get('unit_of_measurement', '')
                })
        
        _LOGGER.info("SmartCasa: Sincronizzazione iniziale di %s entità", len(entities))
        response = await send_to_server({"action": "sync_entities", "entities": entities})
        
        if response and "allowed_entities" in response:
            hass.data[DOMAIN][entry.entry_id]["whitelist"] = response["allowed_entities"]
            _LOGGER.info("SmartCasa: Whitelist ricevuta (%s entità attive)", len(response["allowed_entities"]))

    async def poll_commands_interval(_now):
        """Controlla se AdminLTE ha inviato nuovi comandi."""
        response = await send_to_server({"action": "poll_commands"})
        
        if response and response.get("status") == "success":
            commands = response.get("commands", [])
            for cmd in commands:
                _LOGGER.info("SmartCasa: Esecuzione comando remoto %s su %s", cmd['service'], cmd['entity_id'])
                
                domain, service = cmd['service'].split('.')
                service_data = cmd.get('payload', {}) or {}
                service_data["entity_id"] = cmd['entity_id']
                
                # Esegue il comando in Home Assistant
                await hass.services.async_call(domain, service, service_data)

    # --- AVVIO OPERAZIONI ---
    
    # 1. Sync iniziale
    hass.async_create_task(sync_all_entities())

    # 2. Polling comandi ogni 10 secondi
    async_track_time_interval(hass, poll_commands_interval, timedelta(seconds=10))

    # 3. Listener per i cambi di stato (solo se in Whitelist)
    async def handle_state_change(event: Event):
        new_state = event.data.get("new_state")
        if not new_state or new_state.domain not in SUPPORTED_DOMAINS:
            return

        entity_id = event.data.get("entity_id")
        whitelist = hass.data[DOMAIN][entry.entry_id].get("whitelist", [])

        # Invia l'aggiornamento solo se il server PHP lo ha richiesto (is_active=1)
        if entity_id in whitelist:
            await send_to_server({
                "action": "update_state",
                "entity_id": entity_id,
                "state": new_state.state
            })

    hass.bus.async_listen("state_changed", handle_state_change)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Rimozione dell'integrazione."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True