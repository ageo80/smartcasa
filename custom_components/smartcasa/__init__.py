import logging
import aiohttp
import asyncio
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant, Event
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)
DOMAIN = "smartcasa"

# Domini supportati
SUPPORTED_DOMAINS = ['light', 'cover', 'switch', 'climate', 'sensor', 'binary_sensor']

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    conf = entry.data
    base_url = conf['server_url'].rstrip('/')
    server_url = f"{base_url}/api_bridge.php"
    
    # Stato interno per il debug visivo
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "last_sync": "Mai",
        "status": "Inizializzazione",
        "entities_tracked": 0
    }

    async def send_to_server(payload):
        """Invia dati al server con gestione errori e log di debug."""
        payload.update({
            "token": conf.get('token'), 
            "api_key": conf.get('api_key'),
            "version": "1.0.2"
        })
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(server_url, json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        hass.data[DOMAIN][entry.entry_id]["status"] = "Connesso"
                        hass.data[DOMAIN][entry.entry_id]["last_sync"] = datetime.now().strftime("%H:%M:%S")
                        return data
                    else:
                        _LOGGER.error("Server PHP ha risposto con codice: %s", resp.status)
                        hass.data[DOMAIN][entry.entry_id]["status"] = f"Errore HTTP {resp.status}"
            except Exception as e:
                _LOGGER.error("Errore di connessione verso %s: %s", server_url, e)
                hass.data[DOMAIN][entry.entry_id]["status"] = "Errore Connessione"
        return None

    async def sync_all_entities():
        """Sincronizza le entità e riceve la lista di quelle filtrate dal server."""
        entities = []
        for state in hass.states.async_all():
            if state.domain in SUPPORTED_DOMAINS:
                entities.append({
                    "entity_id": state.entity_id,
                    "friendly_name": state.attributes.get('friendly_name', state.entity_id),
                    "state": state.state,
                    "unit": state.attributes.get('unit_of_measurement', '')
                })
        
        _LOGGER.debug("Sync richiesto per %s entità", len(entities))
        response = await send_to_server({"action": "sync_entities", "entities": entities})
        
        # Se il server risponde con una lista di 'allowed_entities', salviamola
        if response and "allowed_entities" in response:
            hass.data[DOMAIN][entry.entry_id]["whitelist"] = response["allowed_entities"]
            hass.data[DOMAIN][entry.entry_id]["entities_tracked"] = len(response["allowed_entities"])
        else:
            # Se il server non filtra, tracciamo tutto
            hass.data[DOMAIN][entry.entry_id]["whitelist"] = [e["entity_id"] for e in entities]
            hass.data[DOMAIN][entry.entry_id]["entities_tracked"] = len(entities)

    async def poll_commands_interval(_now):
        """Controlla se ci sono comandi pendenti sul server."""
        response = await send_to_server({"action": "poll_commands"})
        if response and response.get("status") == "success":
            for cmd in response.get("commands", []):
                domain, service = cmd['service'].split('.')
                data = cmd.get('payload', {}) or {}
                data["entity_id"] = cmd['entity_id']
                _LOGGER.info("Esecuzione comando remoto: %s", service)
                await hass.services.async_call(domain, service, data)

    # Avvio task iniziali
    hass.async_create_task(sync_all_entities())
    async_track_time_interval(hass, poll_commands_interval, timedelta(seconds=10))

    async def handle_state_change(event: Event):
        """Invia aggiornamenti di stato solo per le entità whitelisted."""
        new_state = event.data.get("new_state")
        if not new_state or new_state.domain not in SUPPORTED_DOMAINS:
            return

        entity_id = event.data.get("entity_id")
        whitelist = hass.data[DOMAIN][entry.entry_id].get("whitelist", [])

        # Controllo: invia al server solo se l'entità è nella whitelist del PHP
        if entity_id in whitelist:
            await send_to_server({
                "action": "update_state",
                "entity_id": entity_id,
                "state": new_state.state,
                "attributes": dict(new_state.attributes)
            })

    hass.bus.async_listen("state_changed", handle_state_change)
    
    # Registra i sensori di diagnostica (opzionale, richiede sensor.py)
    # Per ora li lasciamo nei log di sistema
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Rimuove l'integrazione correttamente."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True