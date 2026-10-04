# bluetti-bt-connect 2.0.5

Requires `bluetti-bt-connect-lib==2.0.4`.

## New: Pack Temperature

A proper temperature sensor for the EP2000's battery pack. The battery
reports it in °F; the integration passes that on as a temperature, and
**Home Assistant shows it in your own unit** - °C on a metric system - in the
dashboard, history and graphs, with no setting needed. You can still pick a
different unit on the entity itself.

How the unit was settled is in bluetti-community/bluetti-registers#42.

## Fixed: Connected Devices (was Total Node Count)

The old **Total Node Count** sensor always showed 0 - the register it read
was never a count. It is replaced by **Connected Devices**, counted from the
battery's own list of devices (EBOX, inverter, battery packs). An EP2000 with
one HV800 pack shows 3.

## read_registers can now read the other devices

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

## Removed

- **Raw Register 6007** and **Raw Register 6115** (added in 2.0.3 for the
  investigation). Their old entities show as unavailable after upgrading;
  delete them from Settings -> Entities.
- **Total Node Count** - replaced as above; delete the old entity the same way.

## Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.4 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.5**.
3. Restart Home Assistant.
