# bluetti-bt-connect 2.0.7

Requires `bluetti-bt-connect-lib==2.0.6`.

## Fixed: Pack Temperature

Pack Temperature was decoded as °F in 2.0.5. BLUETTI's own app decodes the
register as **°C + 40**, so the reading now goes up: a battery that showed
about 19 °C will show about 26 °C. The entity, its history and its unit stay
the same. Only the values change from the update onwards.

## New: home energy from the EBOX

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

## Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.6 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.7**.
3. Restart Home Assistant.
