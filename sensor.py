from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AlleanzaDataCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="latest_bill_total",
        name="Ultima bolletta - Importo totale",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:currency-eur",
    ),
    SensorEntityDescription(
        key="latest_bill_number",
        name="Ultima bolletta - Numero",
        icon="mdi:file-document-outline",
    ),
    SensorEntityDescription(
        key="latest_bill_issue_date",
        name="Ultima bolletta - Data emissione",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:calendar",
    ),
    SensorEntityDescription(
        key="latest_bill_due_date",
        name="Ultima bolletta - Data scadenza",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:calendar-alert",
    ),
    SensorEntityDescription(
        key="latest_bill_period",
        name="Ultima bolletta - Periodo di competenza",
        icon="mdi:calendar-range",
    ),
    SensorEntityDescription(
        key="latest_bill_installments",
        name="Ultima bolletta - Numero rate",
        icon="mdi:credit-card-multiple",
    ),
    SensorEntityDescription(
        key="electricity_amount",
        name="Ultima bolletta - Importo energia elettrica",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
    ),
    SensorEntityDescription(
        key="gas_amount",
        name="Ultima bolletta - Importo gas",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:fire",
    ),
    SensorEntityDescription(
        key="customer_name",
        name="Cliente - Nome e cognome",
        icon="mdi:account",
    ),
    SensorEntityDescription(
        key="customer_fiscal_code",
        name="Cliente - Codice fiscale",
        icon="mdi:card-account-details",
    ),
    SensorEntityDescription(
        key="customer_address",
        name="Cliente - Indirizzo",
        icon="mdi:home",
    ),
    SensorEntityDescription(
        key="customer_phone",
        name="Cliente - Telefono",
        icon="mdi:phone",
    ),
    SensorEntityDescription(
        key="customer_email",
        name="Cliente - Email",
        icon="mdi:email",
    ),
)

SUPPLY_SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="supply_type",
        name="Fornitura - Tipo",
        icon="mdi:transmission-tower",
    ),
    SensorEntityDescription(
        key="supply_code",
        name="Fornitura - Codice fornitura",
        icon="mdi:barcode",
    ),
    SensorEntityDescription(
        key="supply_pod_pdr",
        name="Fornitura - POD/PDR",
        icon="mdi:counter",
    ),
    SensorEntityDescription(
        key="supply_power",
        name="Fornitura - Potenza impegnata",
        icon="mdi:flash",
    ),
    SensorEntityDescription(
        key="supply_meter",
        name="Fornitura - Numero contatore",
        icon="mdi:gauge",
    ),
    SensorEntityDescription(
        key="supply_address",
        name="Fornitura - Indirizzo",
        icon="mdi:map-marker",
    ),
    SensorEntityDescription(
        key="supply_contract",
        name="Fornitura - Numero contratto",
        icon="mdi:file-sign",
    ),
    SensorEntityDescription(
        key="supply_status",
        name="Fornitura - Stato",
        icon="mdi:check-circle",
    ),
    SensorEntityDescription(
        key="supply_frequency",
        name="Fornitura - Frequenza fatturazione",
        icon="mdi:calendar-clock",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AlleanzaDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for description in SENSOR_DESCRIPTIONS:
        entities.append(
            AlleanzaSensor(coordinator, description, entry)
        )

    entities.append(
        AlleanzaSuppliesSensor(coordinator, entry)
    )

    for description in SUPPLY_SENSOR_DESCRIPTIONS:
        for supply_index in range(2):
            entities.append(
                AlleanzaSupplySensor(coordinator, description, entry, supply_index)
            )

    async_add_entities(entities)


class AlleanzaSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: AlleanzaDataCoordinator,
        description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Alleanza Luce e Gas",
            manufacturer="Alleanza Luce e Gas",
            model="Coop",
        )

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if data is None:
            return None
        return self._get_value(data)

    def _get_value(self, data: dict) -> Any:
        bill = data.get("latest_bill")
        customer = data.get("customer")
        key = self.entity_description.key

        if key == "latest_bill_total":
            return bill.get("IMPORTOTOTALE") if bill else None
        if key == "latest_bill_number":
            return bill.get("NUMERO") if bill else None
        if key == "latest_bill_issue_date":
            raw = bill.get("DATAEMISSIONE") if bill else None
            if raw:
                return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            return None
        if key == "latest_bill_due_date":
            raw = bill.get("DATASCADENZA") if bill else None
            if raw:
                return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            return None
        if key == "latest_bill_period":
            if bill:
                start = bill.get("DATACOMPETENZAINI", "")
                end = bill.get("DATACOMPETENZAFIN", "")
                if start and end:
                    s = datetime.fromisoformat(start.replace("Z", "+00:00")).date()
                    e = datetime.fromisoformat(end.replace("Z", "+00:00")).date()
                    return f"{s} → {e}"
            return None
        if key == "latest_bill_installments":
            return bill.get("NUMERORATE") if bill else None
        if key == "electricity_amount":
            return self._get_commodity_amount(bill, "ENELE")
        if key == "gas_amount":
            return self._get_commodity_amount(bill, "GM")
        if key == "customer_name":
            if customer:
                return f"{customer.get('name', '')} {customer.get('surname', '')}"
            return None
        if key == "customer_fiscal_code":
            return customer.get("fiscalCode") if customer else None
        if key == "customer_address":
            if customer:
                res = customer.get("residences", {})
                if res:
                    parts = []
                    if res.get("address"):
                        parts.append(f"Via {res['address']}")
                    if res.get("civicNumber"):
                        parts.append(res["civicNumber"])
                    if res.get("city"):
                        parts.append(res["city"])
                    if res.get("province"):
                        parts.append(f"({res['province']})")
                    if res.get("postalCode"):
                        parts.append(res["postalCode"])
                    return " ".join(parts)
            return None
        if key == "customer_phone":
            return customer.get("phone") if customer else None
        if key == "customer_email":
            return customer.get("communicationEmailAddress") if customer else None
        return None

    @staticmethod
    def _get_commodity_amount(bill: dict | None, commodity: str) -> float | None:
        if not bill:
            return None
        details = bill.get("DETTAGLI", {})
        items = details.get("DETTAGLIODOCUMENTO", [])
        total = 0.0
        for item in items:
            if item.get("COMMODITY") == commodity:
                total += item.get("IMPORTO", 0)
        return total if total > 0 else None

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data
        if data is None:
            return {}
        bill = data.get("latest_bill")
        attrs = {}
        if bill:
            attrs["anno"] = bill.get("ANNO")
            attrs["tipo_documento"] = bill.get("TIPODOCUMENTODESC")
            attrs["id_documento"] = bill.get("IDDOCUMENTO")
            attrs["segmento"] = bill.get("SEGMENTO")
            attrs["commodity"] = bill.get("COMMODITY")
        return attrs


class AlleanzaSuppliesSensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: AlleanzaDataCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_supplies_list"
        self._attr_name = "Elenco forniture"
        self._attr_icon = "mdi:format-list-bulleted"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Alleanza Luce e Gas",
            manufacturer="Alleanza Luce e Gas",
            model="Coop",
        )

    @property
    def native_value(self) -> str:
        data = self.coordinator.data
        if data is None:
            return None
        supplies = data.get("supplies", [])
        if not supplies:
            return "Nessuna fornitura"
        return f"{len(supplies)} forniture"

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data
        if data is None:
            return {}
        supplies = data.get("supplies", [])
        attrs = {}
        for i, s in enumerate(supplies):
            prefix = f"fornitura_{i + 1}"
            attrs[f"{prefix}_tipo"] = s.get("supplyType")
            attrs[f"{prefix}_codice"] = s.get("supplyCode")
            attrs[f"{prefix}_pod_pdr"] = s.get("pod") or s.get("pdr")
            attrs[f"{prefix}_stato"] = s.get("supplyStatus")
            attrs[f"{prefix}_indirizzo"] = s.get("supplyLocationAddress")
            attrs[f"{prefix}_potenza"] = s.get("committedPower")
            attrs[f"{prefix}_contatore"] = s.get("meterNumber")
            attrs[f"{prefix}_contratto"] = s.get("contractNumber")
            attrs[f"{prefix}_frequenza"] = s.get("billingFrequency")
        return attrs


class AlleanzaSupplySensor(CoordinatorEntity, SensorEntity):
    def __init__(
        self,
        coordinator: AlleanzaDataCoordinator,
        description: SensorEntityDescription,
        entry: ConfigEntry,
        supply_index: int,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._supply_index = supply_index
        self._attr_unique_id = f"{entry.entry_id}_{description.key}_{supply_index}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Alleanza Luce e Gas",
            manufacturer="Alleanza Luce e Gas",
            model="Coop",
        )

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if data is None:
            return None
        supplies = data.get("supplies", [])
        if self._supply_index >= len(supplies):
            return None
        supply = supplies[self._supply_index]
        key = self.entity_description.key
        if key == "supply_type":
            st = supply.get("supplyType", "")
            return "Gas" if st == "GAS" else "Luce" if st == "LIGHT" else st
        if key == "supply_code":
            return supply.get("supplyCode")
        if key == "supply_pod_pdr":
            return supply.get("pod") or supply.get("pdr")
        if key == "supply_power":
            p = supply.get("committedPower")
            a = supply.get("availablePower")
            if a and a != "0 kW":
                return f"{p} (disponibile {a})"
            return p
        if key == "supply_meter":
            return supply.get("meterNumber")
        if key == "supply_address":
            return supply.get("supplyLocationAddress")
        if key == "supply_contract":
            return supply.get("contractNumber")
        if key == "supply_status":
            return supply.get("supplyStatus")
        if key == "supply_frequency":
            return supply.get("billingFrequency")
        return None

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data
        if data is None:
            return {}
        supplies = data.get("supplies", [])
        if self._supply_index >= len(supplies):
            return {}
        supply = supplies[self._supply_index]
        return {
            "product_code": supply.get("productCode"),
            "active_from": supply.get("activeFrom"),
            "supply_start_date": supply.get("supplyStartDate"),
            "heating_mode": supply.get("heatingMode"),
            "meter_status": supply.get("meterStatus"),
        }

    @property
    def name(self) -> str:
        supply_type = self._get_supply_type()
        base = self.entity_description.name or ""
        return f"Fornitura {supply_type} - {base}"

    def _get_supply_type(self) -> str:
        data = self.coordinator.data
        if data is None:
            return f"{self._supply_index + 1}"
        supplies = data.get("supplies", [])
        if self._supply_index >= len(supplies):
            return f"{self._supply_index + 1}"
        st = supplies[self._supply_index].get("supplyType", "")
        return "Gas" if st == "GAS" else "Luce" if st == "LIGHT" else f"{self._supply_index + 1}"
