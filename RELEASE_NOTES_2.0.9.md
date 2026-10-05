# bluetti-bt-connect 2.0.9

Requires `bluetti-bt-connect-lib==2.0.8`.

## Fixed: Active Cell Count

**Active Cell Count** was showing the number of temperature sensors in the
battery, not cells: 112 instead of 224 on an HV800 with seven B700 packs. It
now reads the right register. The entity is the same; only its value changes
from the update onwards.

## New and renamed

- **Temperature Sensor Count** (diagnostic): the number of temperature
  sensors across the battery packs (112 on seven B700s).
- **Battery Stack Count** is now named **Battery Modules**. It counts the
  battery modules (one per B700). Same entity, just a clearer name.

## Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.8 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.9**.
3. Restart Home Assistant.
