# bluetti-bt-connect 2.0.3

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

## Upgrading

1. Make sure `bluetti-bt-connect-lib` 2.0.2 is on PyPI.
2. In HACS, update **Bluetti BT Connect** to **2.0.3**.
3. Restart Home Assistant.

The two sensors appear under the device's Diagnostic section.
