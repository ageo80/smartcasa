# 🏠 SmartCasa Bridge for Home Assistant

SmartCasa è un'integrazione personalizzata che permette di collegare il tuo server Home Assistant a una dashboard esterna basata su **PHP e AdminLTE**. 

Il componente sincronizza automaticamente le entità (luci, tapparelle, interruttori) sul tuo database MySQL e permette il controllo remoto bidirezionale senza necessità di aprire porte sul router (tramite polling).

## 🚀 Caratteristiche
- **Auto-Discovery**: Sincronizza automaticamente le entità supportate al primo avvio.
- **Stato in Tempo Reale**: Invia i cambiamenti di stato al server PHP istantaneamente.
- **Controllo Remoto**: Riceve comandi dalla dashboard web (Polling 10s).
- **Integrazione HACS**: Facilmente installabile e aggiornabile.

## 🛠️ Requisiti
- Un server web con **PHP 7.4+** e **MySQL**.
- La cartella `domotica` configurata sul tuo web server con il file `api_bridge.php`.
- [HACS](https://hacs.xyz/) installato su Home Assistant.

## 📦 Installazione tramite HACS

1. Apri Home Assistant e vai su **HACS** > **Integrazioni**.
2. Clicca sui tre puntini in alto a destra e seleziona **Repository personalizzati**.
3. Incolla l'URL di questo repository: `https://github.com/ageo80/smartcasa`
4. Seleziona **Integrazione** come categoria e clicca su **Aggiungi**.
5. Cerca "SmartCasa Bridge" nella lista e clicca su **Installa**.
6. Riavvia Home Assistant.

## ⚙️ Configurazione

Dopo il riavvio:
1. Vai in **Impostazioni** > **Dispositivi e Servizi**.
2. Clicca su **Aggiungi Integrazione** e cerca **SmartCasa**.
3. Inserisci i parametri richiesti:
   - **Nome Casa**: Un nome identificativo.
   - **URL Server**: `https://www.tuosito.it/domotica`
   - **Token**: Il token UUID generato dalla pagina `registra_ha.php`.
   - **API KEY**: La chiave segreta generata dal server.

## 📂 Struttura Database
L'integrazione richiede le tabelle `ha_servers`, `ha_entities` e `ha_commands`. Assicurati di aver eseguito lo script SQL fornito nella documentazione del server.

## 📝 Debug
Per attivare i log dettagliati, aggiungi quanto segue al tuo `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.smartcasa: debug