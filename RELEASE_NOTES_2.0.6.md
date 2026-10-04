# bluetti-bt-connect 2.0.6

Requires `bluetti-bt-connect-lib==2.0.5`.

## Removed: three EP2000 energy sensors that never worked

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

## Want kWh totals?

Home Assistant can work them out from the power sensors. Go to
Settings -> Devices & services -> Helpers -> Create helper -> **Integral**,
and pick a power sensor, for example **Total PV Power** for solar
generation. Use method *Left* and unit prefix *k* to get kWh. The result
works in the Energy dashboard.

## Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.5 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.6**.
3. Restart Home Assistant.
4. Delete the three unavailable entities listed above.
