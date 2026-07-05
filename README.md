# Alleanza Luce e Gas per Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integrazione non ufficiale per **Alleanza Luce e Gas (Coop)** che espone in Home Assistant le **fatture**, i **dettagli cliente** e le **forniture** letti dall'area clienti.

> ⚠️ **Disclaimer**: integrazione non ufficiale, non affiliata ad Alleanza Luce e Gas S.p.A. Le credenziali restano salvate nella tua istanza di Home Assistant (`config_entries` crittografate) e non escono dal tuo sistema.

## Funzionalità

- 🔐 **Config flow UI** con validazione del login (email + password)
- 💶 **Ultima bolletta**: importo totale, numero, date, periodo, rate
- 💡 **Dettaglio energia elettrica**: importo estratto dalla bolletta
- 🔥 **Dettaglio gas**: importo estratto dalla bolletta
- 👤 **Dati cliente**: nome, CF, indirizzo, telefono, email
- 🏠 **Elenco forniture** completo (Luce + Gas)
- ⚡ **Dettaglio forniture**: POD/PDR, potenza, contatore, contratto, frequenza
- 🔄 **Aggiornamento automatico** configurabile (default 6 ore)

## Entità create

### Bolletta

| Entità | Classe | Descrizione |
|--------|--------|-------------|
| `sensor.ultima_bolletta_importo_totale` | Monetario | Importo totale ultima bolletta (€) |
| `sensor.ultima_bolletta_numero` | — | Numero bolletta |
| `sensor.ultima_bolletta_data_emissione` | Data | Data emissione |
| `sensor.ultima_bolletta_data_scadenza` | Data | Data scadenza |
| `sensor.ultima_bolletta_periodo_competenza` | — | Periodo di competenza (es. 2026-04-01 → 2026-04-30) |
| `sensor.ultima_bolletta_numero_rate` | — | Numero rate |
| `sensor.ultima_bolletta_importo_energia_elettrica` | Monetario | Importo energia elettrica (€) |
| `sensor.ultima_bolletta_importo_gas` | Monetario | Importo gas (€) |

### Cliente

| Entità | Classe | Descrizione |
|--------|--------|-------------|
| `sensor.cliente_nome_cognome` | — | Nome e cognome |
| `sensor.cliente_codice_fiscale` | — | Codice fiscale |
| `sensor.cliente_indirizzo` | — | Indirizzo di residenza |
| `sensor.cliente_telefono` | — | Numero di telefono |
| `sensor.cliente_email` | — | Email |

### Forniture

| Entità | Classe | Descrizione |
|--------|--------|-------------|
| `sensor.elenco_forniture` | — | Riepilogo forniture (in attributi tutti i dettagli) |
| `sensor.fornitura_{luce/gas}_tipo` | — | Tipo fornitura |
| `sensor.fornitura_{luce/gas}_codice_fornitura` | — | Codice fornitura |
| `sensor.fornitura_{luce/gas}_pod_pdr` | — | POD (Luce) / PDR (Gas) |
| `sensor.fornitura_{luce/gas}_potenza_impegnata` | — | Potenza impegnata |
| `sensor.fornitura_{luce/gas}_numero_contatore` | — | Numero contatore |
| `sensor.fornitura_{luce/gas}_indirizzo` | — | Indirizzo di fornitura |
| `sensor.fornitura_{luce/gas}_numero_contratto` | — | Numero contratto |
| `sensor.fornitura_{luce/gas}_stato` | — | Stato fornitura |
| `sensor.fornitura_{luce/gas}_frequenza_fatturazione` | — | Frequenza fatturazione |

## Installazione

### HACS (consigliato)

1. In HACS → **Integrazioni** → ⋮ → **Archivi personalizzati**
2. Aggiungi: `https://github.com/fab92io/ha-alleanza-luce-gas`
3. Categoria: **Integrazione**
4. Cerca "Alleanza Luce e Gas" e installa
5. Riavvia Home Assistant
6. **Impostazioni** → **Dispositivi e servizi** → **Aggiungi integrazione** → "Alleanza Luce e Gas"

### Manuale

Copia la cartella `custom_components/alleanza_luce_gas/` in `<config>/custom_components/alleanza_luce_gas/` e riavvia Home Assistant.

## Configurazione

Nel flow di configurazione inserisci:

- **Email** dell'area clienti
- **Password** dell'area clienti
- **Intervallo aggiornamento** (ore, predefinito 6, min 1, max 48)

### Modificare le impostazioni

1. **Impostazioni → Dispositivi e servizi** → clicca sull'integrazione **Alleanza Luce e Gas**
2. Pulsante **Configura** (ingranaggio)
3. Modifica **Intervallo di aggiornamento** → **Salva**

## Esempi Lovelace

```yaml
type: entities
title: Alleanza Luce e Gas - Bolletta
entities:
  - sensor.ultima_bolletta_importo_totale
  - sensor.ultima_bolletta_importo_energia_elettrica
  - sensor.ultima_bolletta_importo_gas
  - sensor.ultima_bolletta_numero
  - sensor.ultima_bolletta_data_emissione
  - sensor.ultima_bolletta_data_scadenza
  - sensor.ultima_bolletta_periodo_competenza
  - sensor.ultima_bolletta_numero_rate
```

```yaml
type: entities
title: Alleanza Luce e Gas - Forniture
entities:
  - sensor.elenco_forniture
  - sensor.fornitura_luce_tipo
  - sensor.fornitura_luce_pod_pdr
  - sensor.fornitura_luce_potenza_impegnata
  - sensor.fornitura_gas_tipo
  - sensor.fornitura_gas_pod_pdr
  - sensor.fornitura_gas_potenza_impegnata
```

## Esempio automazione

```yaml
alias: "Nuova bolletta - Notifica"
trigger:
  platform: state
  entity_id: sensor.ultima_bolletta_numero
action:
  service: notify.mobile_app_iphone
  data:
    title: "Nuova bolletta Alleanza Luce e Gas"
    message: >-
      Importo: {{ states('sensor.ultima_bolletta_importo_totale') }}€ -
      Scadenza: {{ state_attr('sensor.ultima_bolletta_data_scadenza', 'state') }}
```

## Sviluppo

```
custom_components/alleanza_luce_gas/
├── __init__.py         # Setup entry + coordinator
├── api.py              # Client API (login, GraphQL, fatture)
├── config_flow.py      # Flow UI configurazione
├── const.py            # Costanti
├── coordinator.py      # DataUpdateCoordinator
├── sensor.py           # Tutti i sensori
├── services.yaml       # Servizi (force_update)
├── manifest.json
├── strings.json
└── translations/
    └── it.json
```

## Licenza

MIT — vedi [LICENSE](LICENSE).
