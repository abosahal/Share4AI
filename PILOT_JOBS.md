# Authenticated job pilot — 2026-09-10

## What changed

The Provider App now contains an outbound job worker. A client submits text to the pilot Control Plane, the provider polls for one signed task, and tokens return through the Control Plane as SSE. No inbound port on the provider. Customer text does not enter Local AI history, desktop events or logs.

Start Sharing requires a live runtime, passing benchmark and provider credential. AVAILABLE additionally requires eligible telemetry and an active worker. Stop Sharing disables admission first and cancels active network inference. A blocked inference read is interrupted by terminating the owned runtime; **restart Local AI and rerun benchmark after cancellation before sharing again**. Opening Local AI chat stops sharing first so the owner has priority.

This is an **in-memory, loopback-only, one-trusted-provider pilot**, not the persistent production router. The existing `dev_control_plane.py` remains a registration-only fixture; use the new pilot for jobs. Do not expose either server to the Internet.

## Windows test on the machine with the model

Use Python 3.11+ with Tcl/Tk. No extra packages or LM Studio required. In PowerShell, from the Share4AI directory, choose two different long random secrets for this test. Use the provider secret only for the server and Provider App, and the client secret only for the server and test client. Do not commit or send these secrets in chat.

**Terminal 1 — Control Plane**

```powershell
$env:SHARE4AI_PROVIDER_TOKEN = Read-Host 'Provider test secret'
$env:SHARE4AI_CLIENT_TOKEN = Read-Host 'Different client test secret'
py -3 -m tools.pilot_control_plane
```

**Terminal 2 — Provider**

```powershell
$env:SHARE4AI_PROVIDER_TOKEN = Read-Host 'Same provider test secret'
py -3 -m provider
```

Use Scan → Download & Verify → Start Local AI → Benchmark. Set Control Plane to `http://127.0.0.1:8000`. Start Sharing after benchmark passes. CPU-only or slow devices are not made eligible merely to force a successful demo.

**Terminal 3 — Client**

```powershell
$env:SHARE4AI_CLIENT_TOKEN = Read-Host 'Same client test secret'
py -3 -m tools.pilot_chat
```

The client reads the installed model fingerprint automatically on the same machine, asks for a message, and displays streamed output. If the provider uses a custom data directory, pass `--state-dir PATH`; alternatively pass `--model-sha256 HASH` from its installed manifest.

While a response is being generated, press Stop Sharing in the provider. The client must receive a terminal error, not a successful partial answer. To retry after cancellation, start the runtime, run benchmark, and enable sharing again. Closing the client also cancels its task; detection is normally within the keepalive/poll intervals plus network timeout.

## Protocol and limits

- Provider bearer and client bearer are separate. The pilot binds its provider credential to the first registered node until server restart. Production needs enrollment, per-node keys, revocation and TLS termination.
- `POST /v1/chat/stream`: client authorization; text messages, exact `model_sha256`, and `max_tokens`. Missing/ineligible node or full single slot returns 409 before streaming.
- `POST /v1/jobs/poll`: authenticated provider pulls one lease; no job can be claimed twice.
- Envelope: HMAC-SHA256 with a domain prefix over the entire canonical JSON job. Includes node ID, exact model SHA256, job ID, issue/expiry, messages and output limit. The worker verifies before executing. This is **job authorization**, separate from artifact/application signing.
- `POST /v1/jobs/event`: authenticated node + job signature + monotonically ordered sequence. `token`, `done` or `error`. Duplicates, wrong job authorization and events after closure are rejected. No unsafe retry after an ambiguous event write; job fails instead of duplicating text.
- `POST /v1/jobs/status`: cancellation/deadline monitoring. Unknown lease, network failure or cancellation stops inference. Separate registration heartbeat continues during execution.
- Pilot deadline 120 seconds, verifier maximum 180 seconds, node TTL 20 seconds, one active job, 40 messages / 12,000 characters, maximum 1,024 output tokens, 64KiB request, 512 stream events / 256KiB response buffer. Backpressure overflow cancels the job.
- No automatic failover after partial output; error is explicit. No silent merging of two answers and no billing claims.
- Prompts are erased when jobs finish and buffers removed when the streaming consumer exits. No persistence/recovery on server restart. Python/GPU memory wiping is not guaranteed.

## Validation

Automated tests cover real HTTP provider polling and client SSE against the broker, with a deterministic test runtime: complete response, mid-stream Stop, lost lease, auth separation, signed payload tampering, expiry, wrong node/model, replay, ordering, stale provider and prompt cleanup. These demonstrate orchestration, **not Qwen inference or GPU performance**. Earlier hardware/Tcl limitations still apply to this execution environment.

Run `py -3 -m unittest discover -s tests -v`. Next hardware acceptance: real Qwen response, Stop during prefill and generation, client disconnect, server shutdown/restart, and owner Local AI use. Multi-node routing, production persistence, broader live load control and signed Windows distribution remain future milestones.
