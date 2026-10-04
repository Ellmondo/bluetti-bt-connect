# bluetti-bt-connect 2.0.4

A new **read-only** action, `bluetti_bt_connect.read_registers`, for exploring
registers the integration does not decode yet. Requires
`bluetti-bt-connect-lib==2.0.3`.

## What it does

Reads a block of up to 32 registers from the battery once and returns the raw
values - each one unsigned, signed and in hex. It cannot change anything: the
library only ever sends a Modbus *read* (function 3) for it, at the same slave
normal polling reads from.

It shares the integration's connection and lock, so it never interleaves with
a poll or a write, and it never opens a second Bluetooth connection.

## How to use it

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

## Leads worth reading

From Ellmondo/bluetti-bt-connect-lib#2 (unverified on an EP2000, so read them
before trusting them): **1700** meter info and **1900** meter settings,
**5800-5802** EMS scheduling, **2211/2212** charge voltage and current,
**2219** PV parallel mode, **2244** CT ratio, **21000** node list.

Reading is always safe. Do not write to any of these from automations or
scripts based on what you find - several registers in this range change how
the unit behaves on the grid.
