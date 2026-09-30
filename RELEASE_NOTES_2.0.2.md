# bluetti-bt-connect 2.0.2

**The Bluetooth connection is now closed cleanly when Home Assistant stops,
restarts or reloads the integration.**

## Why

The integration holds one Bluetooth connection open permanently, and the
EP2000 accepts only one connection at a time. Until now, a restart simply cut
that link wherever it was - possibly in the middle of a reading or a write.
A cut like that can leave the battery believing the old connection is still
there, so it refuses every new one and the integration never comes back
until the battery itself is restarted.

## What changed

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

## Restarting from Docker

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

## Upgrading

1. In HACS, update **Bluetti BT Connect** to **2.0.2**.
2. Restart Home Assistant.

This first restart is still the old code shutting down. The clean close takes
effect from the next restart onwards.
