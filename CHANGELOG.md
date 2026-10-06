# Changelog: Bluetti BT Connect

Newest first. Each section is also published as the GitHub release for that version. Library changes are in the [library changelog](https://github.com/Ellmondo/bluetti-bt-connect-lib/blob/main/CHANGELOG.md).

## 2.0.9 (2026-10-05)

Requires `bluetti-bt-connect-lib==2.0.8`.

### Fixed: Active Cell Count

**Active Cell Count** was showing the number of temperature sensors in the
battery, not cells: 112 instead of 224 on an HV800 with seven B700 packs. It
now reads the right register. The entity is the same; only its value changes
from the update onwards.

### New and renamed

- **Temperature Sensor Count** (diagnostic): the number of temperature
  sensors across the battery packs (112 on seven B700s).
- **Battery Stack Count** is now named **Battery Modules**. It counts the
  battery modules (one per B700). Same entity, just a clearer name.

### Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.8 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.9**.
3. Restart Home Assistant.

## 2.0.8 (2026-10-05)

Requires `bluetti-bt-connect-lib==2.0.7`.

A large monitoring release for the EP2000. Everything new is read the way
BLUETTI's own app reads it and was checked against a real system. Nothing new
writes to the battery.

### New: status and alarms

- **Inverter Status**: Off, Off-grid, Grid connected, Grid connected (charging / discharging), Error and so on.
- **Battery Status**: Idle, Charging or Discharging.
- **Battery Time Remaining**: minutes until full, or until empty, depending on direction.
- **Active Alarms**: the inverter's current warnings and faults, by code and description, e.g. `B104 PV2 Voltage Low`, or `None`.
- **Problem** (binary sensor): on when any alarm, or an IoT, battery or meter error, is active. Good for a notification automation.
- Diagnostic: **Alarm Count**, **System Error**.

### New: AC-coupled solar

For systems with an existing solar inverter (for example Enphase) on the AC
side, measured through the EBOX's AC PV meter:

- **AC-Coupled Solar Power**: total.
- **AC-Coupled Solar L1 / L2 / L3 Power**, plus per-phase voltage (diagnostic).

On systems without an AC PV meter these read 0 W.

### New: schedule (read-only)

- **Time Control**: whether the Custom-mode schedule is on.
- **Schedule Slot 1–6**: each slot as text, e.g. `Charge 11:01-13:59`, `Discharge 18:00-21:00`, or `Off`.

Editing the schedule from Home Assistant will come in a later release.

### New: diagnostics

**Firmware ARM / DSP / IoT**, **WiFi Signal** (dBm), **Cloud Connected**,
**EMS Control Mode**, and the BMS's **Max Charge Current** and **Max
Discharge Current**.

### Changed

- **Working Mode** now knows **SELF_CONSUMPTION_EXPORT** (self-consumption with export), which BLUETTI offers only on the EP2000. Before, the select went blank whenever that mode was set.
- **AI / EMS control switch** now refuses to change anything while the battery is under cloud control (VPP or dynamic pricing). Switching it off in that state would have silently ended the cloud mode. The **EMS Control Mode** sensor shows which mode is active.

### Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.7 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.8**.
3. Restart Home Assistant.

Each poll now makes eight more Bluetooth requests to the EBOX, all to ranges
a real unit is known to serve.

## 2.0.7 (2026-10-05)

Requires `bluetti-bt-connect-lib==2.0.6`.

### Fixed: Pack Temperature

Pack Temperature was decoded as °F in 2.0.5. BLUETTI's own app decodes the
register as **°C + 40**, so the reading now goes up: a battery that showed
about 19 °C will show about 26 °C. The entity, its history and its unit stay
the same. Only the values change from the update onwards.

### New: home energy from the EBOX

On an EP2000 system the EBOX keeps the household totals that the inverter
doesn't. The integration now reads them from the EBOX as well:

- **Home Load Power**: what the house is using right now, in W
- **Self-Sufficiency**: the share of consumption covered without the grid, in %
- **Home Consumption Energy**: lifetime total, in kWh
- **Solar Energy**: lifetime total, in kWh
- **Grid Import Energy**: lifetime total, in kWh
- **Grid Export Energy**: lifetime total, in kWh

The four energy sensors are lifetime counters that only go up, matching the
lifetime statistics in the BLUETTI app. They can go straight into the Energy
dashboard: Settings -> Dashboards -> Energy, with **Grid Import Energy** as
grid consumption, **Grid Export Energy** as return to grid, and **Solar
Energy** as solar production.

They replace the Total AC Consumption and Total Grid Feed-In sensors removed
in 2.0.6. Those only ever showed 0 because they were read from the inverter
instead of the EBOX.

### Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.6 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.7**.
3. Restart Home Assistant.

## 2.0.6 (2026-10-05)

Requires `bluetti-bt-connect-lib==2.0.5`.

### Removed: three EP2000 energy sensors that never worked

- **Total AC Consumption**
- **Total Grid Feed-In**
- **Generated Electricity**

All three read 0 through more than a week of normal running, including
days of solar generation, both in Home Assistant history and in direct
register reads. The battery doesn't hold those totals in the registers they
were read from, so the sensors could only ever show 0.

Their old entities show as unavailable after upgrading. Delete them from
Settings -> Entities.

Other models that report **Generated Electricity** keep it.

### Want kWh totals?

Home Assistant can work them out from the power sensors. Go to
Settings -> Devices & services -> Helpers -> Create helper -> **Integral**,
and pick a power sensor, for example **Total PV Power** for solar
generation. Use method *Left* and unit prefix *k* to get kWh. The result
works in the Energy dashboard.

### Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.5 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.6**.
3. Restart Home Assistant.
4. Delete the three unavailable entities listed above.

## 2.0.5 (2026-10-04)

Requires `bluetti-bt-connect-lib==2.0.4`.

### New: Pack Temperature

A proper temperature sensor for the EP2000's battery pack. The battery
reports it in °F; the integration passes that on as a temperature, and
**Home Assistant shows it in your own unit** - °C on a metric system - in the
dashboard, history and graphs, with no setting needed. You can still pick a
different unit on the entity itself.

How the unit was settled is in bluetti-community/bluetti-registers#42.

### Fixed: Connected Devices (was Total Node Count)

The old **Total Node Count** sensor always showed 0 - the register it read
was never a count. It is replaced by **Connected Devices**, counted from the
battery's own list of devices (EBOX, inverter, battery packs). An EP2000 with
one HV800 pack shows 3.

### read_registers can now read the other devices

The action gains a `slave` option (default 1, the inverter, as before). Any
other address must appear in the battery's own node list - the action reads
that list first and refuses an address that is not on it, so it can never
probe a device that does not exist. On an EP2000 system that allows **0**
(the EBOX) and **41** (the HV800 battery pack). Still read-only.

```yaml
action: bluetti_bt_connect.read_registers
data:
  slave: 41
  address: 6100
  count: 32
```

### Removed

- **Raw Register 6007** and **Raw Register 6115** (added in 2.0.3 for the
  investigation). Their old entities show as unavailable after upgrading;
  delete them from Settings -> Entities.
- **Total Node Count** - replaced as above; delete the old entity the same way.

### Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.4 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.5**.
3. Restart Home Assistant.

## 2.0.4 (2026-10-04)

A new **read-only** action, `bluetti_bt_connect.read_registers`, for exploring
registers the integration does not decode yet. Requires
`bluetti-bt-connect-lib==2.0.3`.

### What it does

Reads a block of up to 32 registers from the battery once and returns the raw
values - each one unsigned, signed and in hex. It cannot change anything: the
library only ever sends a Modbus *read* (function 3) for it, at the same slave
normal polling reads from.

It shares the integration's connection and lock, so it never interleaves with
a poll or a write, and it never opens a second Bluetooth connection.

### How to use it

**Developer Tools -> Actions**, choose **Bluetti BT Connect: Read registers**:

```yaml
action: bluetti_bt_connect.read_registers
data:
  address: 1700
  count: 32
```

The response looks like:

```yaml
address: 1700
count: 32
outcome: ok
registers:
  - address: 1700
    value: 2415
    signed: 2415
    hex: "0x096f"
  ...
```

`outcome` is one of:

| outcome | meaning |
|---|---|
| `ok` | the battery answered; values are in `registers` |
| `refused` | the battery rejected the address range; see `exception_code` (`0x02` = address not served) |
| `no_reply` | the battery stayed silent - some addresses are answered this way |
| `not_connected` / `error` | no connection, or the link dropped mid-read |

A refusal or silence is a normal answer when exploring, not a fault, and the
regular polling carries on unaffected.

`config_entry_id` is only needed if more than one Bluetti is set up. The
action is refused while the Bluetooth connection is released with the hold
switch, so it never takes the battery back from the Bluetti app.

### Leads worth reading

From Ellmondo/bluetti-bt-connect-lib#2 (unverified on an EP2000, so read them
before trusting them): **1700** meter info and **1900** meter settings,
**5800-5802** EMS scheduling, **2211/2212** charge voltage and current,
**2219** PV parallel mode, **2244** CT ratio, **21000** node list.

Reading is always safe. Do not write to any of these from automations or
scripts based on what you find - several registers in this range change how
the unit behaves on the grid.

## 2.0.3 (2026-10-04)

Two new diagnostic sensors for the EP2000, to look for the battery pack
temperature. Requires `bluetti-bt-connect-lib==2.0.2`.

| sensor | register |
|---|---|
| Raw Register 6007 | 6007, pack main-info block |
| Raw Register 6115 | 6115, directly after pack SOH |

Both show the value **exactly as the battery sends it** - no unit, scaling or
offset - because what they hold is not confirmed yet. They sit under
**Diagnostic** on the device page. The purpose is a side-by-side comparison
with `b_t_avg` from a Modbus TCP read of the same unit
(bluetti-community/bluetti-registers#42).

Neither address had been read on this device before, so they are read
carefully: on their own, after the rest of each poll, and dropped until the
next restart if the battery refuses or ignores them. In that case the sensor
stays **unavailable** and nothing else is affected. Read-only - nothing is
written to the battery.

### Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.2 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.3**.
3. Restart Home Assistant.

The two sensors appear under the device's Diagnostic section.

## 2.0.2 (2026-09-30)

**The Bluetooth connection is now closed cleanly when Home Assistant stops,
restarts or reloads the integration.**

### Why

The integration holds one Bluetooth connection open permanently, and the
EP2000 accepts only one connection at a time. Until now, a restart simply cut
that link wherever it was - possibly in the middle of a reading or a write.
A cut like that can leave the battery believing the old connection is still
there, so it refuses every new one and the integration never comes back
until the battery itself is restarted.

### What changed

- **On shutdown and restart** the integration waits for any reading or write
  already in progress to finish, then unsubscribes and disconnects properly.
- **On reload or removal** the same clean close is used. Previously a reload
  could also cut a reading off part-way.
- **The wait is capped at 5 seconds**, so a connection attempt that is still
  retrying can never hold up Home Assistant's shutdown.
- **Nothing reconnects once the link is closed.** Scheduled readings and
  automation writes are held off for the rest of the shutdown.

No library change: still requires `bluetti-bt-connect-lib==2.0.0`. Entities
and entity IDs are unchanged.

### Restarting from Docker

`docker restart`, `docker compose restart`/`stop` and a normal host reboot
all trigger Home Assistant's own shutdown, so the clean close runs.
`docker kill`, `docker rm -f` and anything with `-t 0` do not.

Docker force-stops a container after 10 seconds by default. To give Home
Assistant room when many integrations are shutting down, set this on the
Home Assistant service in your compose file:

```yaml
    stop_grace_period: 2m
```

It is only a ceiling - a normal shutdown still takes a few seconds.

### Upgrading

1. In HACS, update **Bluetti BT Connect** to **2.0.2**.
2. Restart Home Assistant.

This first restart is still the old code shutting down. The clean close takes
effect from the next restart onwards.

## 2.0.0 (2026-09-21)

**Local control of the Bluetti EP2000 works.** Grid import/export limits, working
mode and the switches now write and persist over local Bluetooth. The
long-standing "accepted but silently reverts" behaviour is fixed.

### What changed

- **Requires `bluetti-bt-connect-lib==2.0.0`**, which contains the real fix:
  settings writes now go to **Modbus slave 0** (the device's settings controller)
  instead of slave 1 (the inverter, which echoed writes and then overwrote them).
  See the [library 2.0.0 notes](https://github.com/Ellmondo/bluetti-bt-connect-lib/blob/main/CHANGELOG.md#200-2026-09-21)
  for the full investigation.
- **New "AI Control Mode" switch** (register 2241). When on, Bluetti's AI/EMS
  manages the system and overrides your manual settings; off = manual control.
  If settings ever stop sticking, this is the first thing to check.
- **Max Grid Import Power / Current entities now appear** - their read bounds were
  too low and had been discarding the device's real values (8600 W / 45 A).
- **Removed the "Bluetooth settings password" option** added in 1.8.0. It was
  based on a misread (register 7 sets the BT password; it is not a login) and did
  nothing useful.

### EP2000 controls

AC Output, Charge From Grid, Grid Export (switches); Max Grid Export Power/Current
and Max Grid Import Power/Current (numbers); Working Mode (select); AI Control Mode
(switch). All write and persist over local BLE.

### Upgrading

1. In HACS, update **Bluetti BT Connect** to **2.0.0**.
2. Restart Home Assistant (Home Assistant reinstalls the pinned library on
   restart, so this is required to pull lib 2.0.0).
3. Set a grid limit or working mode and confirm it holds after a poll cycle.

Notes:
- After a write, allow a few seconds for the value to settle before trusting the
  read-back - it propagates from the settings controller back to the reading.
- Keep **AI Control Mode** off for manual control.
- **Grid export and grid-protection settings are regulated for grid-interconnection
  safety in many jurisdictions.** Know your local rules before changing them.

### Credits

Fork of [hassio-bluetti-bt](https://github.com/Patrick762/hassio-bluetti-bt) by
[Patrick762](https://github.com/Patrick762), paired with the
[bluetti-bt-connect-lib](https://github.com/Ellmondo/bluetti-bt-connect-lib)
fork. All credit for the original integration and protocol work to Patrick762 and
the upstream contributors.
