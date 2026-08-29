# PIOS GitHub Connector

Read-connector service. Stores an encrypted GitHub PAT (Fernet vault), pulls
review-requests + my open PRs, and lands them as timestamped, de-duplicated
signals in its own store — the read surface the proactive watcher (M-C) and the
memory spine (M-A) will consume later.

Reachable only through the gateway (no published host port). Requires
`CONNECTOR_VAULT_KEY` (url-safe base64, 32 bytes); the service refuses to start
without it.
