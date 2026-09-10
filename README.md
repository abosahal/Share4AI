# Share4AI

**Community-powered AI** — Windows Provider App v1.1 alpha.

توثيق المشروع وبداية Sprint 1. يعمل التطبيق مع llama.cpp دون LM Studio. هذه نسخة تطوير محلية وليست خدمة عامة جاهزة.

## Quick start — Windows x64

1. Install Python 3.11+ from python.org, including **Tcl/Tk** and the **Python launcher**.
2. Double-click `run_windows.bat` (or run `py -3 -m provider`). No pip packages are required.
3. **Scan → Download & Verify → Start Local AI → Benchmark**.
4. Use the **Local AI** tab. Qwen downloads are about 2.7GB (4B) or 5.7GB (9B); the app selects based on available memory. CUDA runtime packages add about 646MB. Close other memory-heavy applications first.
5. **Cancel / Stop AI** cancels work and stops the owned runtime. Retry restarts interrupted downloads; byte-range resume is not yet implemented.

CPU fallback is for Local AI trials. NVIDIA sharing eligibility requires live telemetry and a passing benchmark. Unsupported hardware or low memory produces an explanation rather than pretending setup succeeded.

## What works in this slice

- Windows CPU/RAM/disk discovery and NVIDIA GPU/VRAM/utilization/temperature detection.
- Pinned Qwen3.5 4B/9B Q4_K_M catalog and llama.cpp b10868 CPU/CUDA 12.4 packages, including CUDA DLLs.
- HTTPS downloads, size/SHA256 checks, safe staged extraction, cancellation and safe retry, optional pinned-publisher Authenticode verification.
- RuntimeAdapter, owned loopback llama-server with per-process API key, streaming Local AI and warm benchmark with real token usage.
- Desktop setup/chat/settings, owner resource threshold, persistent node ID, outbound registration/heartbeat/re-registration and Stop.

## Deliberate alpha limits

**Start Sharing now supports authenticated outbound jobs in a local pilot.** It requires a running model, passing benchmark, eligible telemetry and a provider credential. Stop Sharing cancels active network work; Local AI use stops sharing first. Follow [PILOT_JOBS.md](PILOT_JOBS.md) for the Control Plane and streaming test client. Max GPU Usage is an admission threshold, **not a hard percentage cap**. Full gaming detection, live resource preemption, persistent production Control Plane, multi-node routing and signed installer remain on the roadmap.

The pinned artifacts publish SHA256 digests; detached signatures were not supplied in the catalog. Hash verification is implemented; do not claim signature verification occurred when none was published. Unsloth supplies the GGUF quantizations of upstream Qwen models, rather than an official Qwen GGUF repository. Retain upstream notices when distributing.

Local chat content stays in process memory. No cloud inference or mandatory paid API. Do not use this alpha for sensitive community workloads. See SECURITY_BASELINE.md for the limits of privacy on a provider-owned computer.

## Local Control Plane protocol test

For job execution use `py -3 -m tools.pilot_control_plane` and `py -3 -m tools.pilot_chat` with separate provider/client credentials as described in PILOT_JOBS.md. The older `tools/dev_control_plane.py` remains a registration-only test fixture; it never dispatches jobs. Both bind loopback only and have no persistent storage. A remote endpoint must use HTTPS plus `SHARE4AI_PROVIDER_TOKEN`; production enrollment and per-provider key lifecycle remain future work.

## Development and checks

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m provider --scan --state-dir .state
py -3 -m compileall -q provider tools tests
```

App data defaults to `%LOCALAPPDATA%\Share4AI`; use `--state-dir` for an isolated test. Settings contain no token. Models and runtime archives are never committed. `tools/pin_catalog.py` is maintainer-only and must be reviewed before a catalog update; the app never follows latest automatically.

## Project documents

- [PROJECT_BASELINE.md](PROJECT_BASELINE.md): accepted decisions, provenance, scope and open decisions.
- [ARCHITECTURE.md](ARCHITECTURE.md): components, state and protocol.
- [SECURITY_BASELINE.md](SECURITY_BASELINE.md): trust boundaries and release gates.
- [ROADMAP.md](ROADMAP.md): staged delivery and acceptance.
- [SPRINT_01.md](SPRINT_01.md): current progress and validation limitations.

## Upstream references

- [llama.cpp pinned release](https://github.com/ggml-org/llama.cpp/releases/tag/b10868)
- [llama.cpp server interface](https://github.com/ggml-org/llama.cpp/blob/b10868/tools/server/README.md)
- [Qwen3.5 4B GGUF](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF)
- [Qwen3.5 9B GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF)

Original prototype ZIPs were not present in the repository. The baseline records earlier user-reported success separately from tests of this new implementation.
