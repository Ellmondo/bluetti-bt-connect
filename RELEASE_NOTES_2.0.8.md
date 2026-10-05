# bluetti-bt-connect 2.0.8

Requires `bluetti-bt-connect-lib==2.0.7`.

A large monitoring release for the EP2000. Everything new is read the way
BLUETTI's own app reads it and was checked against a real system. Nothing new
writes to the battery.

## New: status and alarms

- **Inverter Status**: Off, Off-grid, Grid connected, Grid connected (charging / discharging), Error and so on.
- **Battery Status**: Idle, Charging or Discharging.
- **Battery Time Remaining**: minutes until full, or until empty, depending on direction.
- **Active Alarms**: the inverter's current warnings and faults, by code and description, e.g. `B104 PV2 Voltage Low`, or `None`.
- **Problem** (binary sensor): on when any alarm, or an IoT, battery or meter error, is active. Good for a notification automation.
- Diagnostic: **Alarm Count**, **System Error**.

## New: AC-coupled solar

For systems with an existing solar inverter (for example Enphase) on the AC
side, measured through the EBOX's AC PV meter:

- **AC-Coupled Solar Power**: total.
- **AC-Coupled Solar L1 / L2 / L3 Power**, plus per-phase voltage (diagnostic).

On systems without an AC PV meter these read 0 W.

## New: schedule (read-only)

- **Time Control**: whether the Custom-mode schedule is on.
- **Schedule Slot 1–6**: each slot as text, e.g. `Charge 11:01-13:59`, `Discharge 18:00-21:00`, or `Off`.

Editing the schedule from Home Assistant will come in a later release.

## New: diagnostics

**Firmware ARM / DSP / IoT**, **WiFi Signal** (dBm), **Cloud Connected**,
**EMS Control Mode**, and the BMS's **Max Charge Current** and **Max
Discharge Current**.

## Changed

- **Working Mode** now knows **SELF_CONSUMPTION_EXPORT** (self-consumption with export), which BLUETTI offers only on the EP2000. Before, the select went blank whenever that mode was set.
- **AI / EMS control switch** now refuses to change anything while the battery is under cloud control (VPP or dynamic pricing). Switching it off in that state would have silently ended the cloud mode. The **EMS Control Mode** sensor shows which mode is active.

## Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.7 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.8**.
3. Restart Home Assistant.

Each poll now makes eight more Bluetooth requests to the EBOX, all to ranges
a real unit is known to serve.
