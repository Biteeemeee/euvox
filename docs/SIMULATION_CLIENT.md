# Simulation Client

## Purpose

The simulation client is a Windows worker that executes EU5 simulation jobs assigned by the server.

The client is intentionally dumb. It does not optimize, evaluate final scores, or mutate mods.

## Responsibilities

```text
- register with control-api
- report capabilities and heartbeat
- claim simulation jobs
- download mod artifact and baseline save
- verify artifact hashes
- install/activate test mod
- start EU5 in debug mode
- load prepared baseline save
- switch to observer mode
- run/tick the simulation
- create periodic save snapshots
- collect logs and crash data
- upload artifacts
- report completion/failure
```

## Recommended MVP Strategy

Do not automate "new game" from the EU5 main menu for MVP.

Instead:

```text
1. Use versioned baseline saves.
2. Client copies baseline save into save directory.
3. Client starts EU5 in debug mode.
4. Client loads baseline save through console automation.
5. Client activates observe mode.
6. Client runs and snapshots.
```

This avoids fragile GUI automation.

## Client Components

```text
ClientApp
  orchestrates the local job lifecycle

ControlApiClient
  talks to server

ArtifactClient
  downloads/uploads artifacts

Eu5InstallationDetector
  finds eu5.exe, user dir, save dir, log dir

ModInstaller
  installs test mod and verifies hash

Eu5ProcessRunner
  starts and monitors EU5 process

ConsoleController
  sends console commands via UI automation or clipboard

SavegameManager
  manages baseline saves and output snapshots

LogMonitor
  tails error.log and other logs

CrashMonitor
  detects process exit, hangs, timeouts

RunManifestWriter
  writes local manifest for upload
```

## Job Lifecycle

```text
claim job
→ prepare working directory
→ download artifacts
→ verify hashes
→ install mod
→ copy baseline save
→ start EU5 -debug_mode
→ wait for ready state
→ load save
→ observe
→ run until end date
→ save snapshots
→ collect logs
→ upload artifacts
→ report status
→ cleanup
```

## Failure Modes

Report structured failures:

```text
DOWNLOAD_FAILED
HASH_MISMATCH
MOD_INSTALL_FAILED
EU5_START_FAILED
CONSOLE_UNAVAILABLE
SAVE_LOAD_FAILED
SIMULATION_TIMEOUT
PROCESS_CRASHED
NO_SNAPSHOT_PROGRESS
UPLOAD_FAILED
```

## Heartbeat

Client heartbeat should include:

```json
{
  "client_id": "win-sim-01",
  "status": "running",
  "job_id": "job_001",
  "current_phase": "simulation",
  "current_game_date": "1500.1.1",
  "last_snapshot_at": "...",
  "eu5_process_alive": true
}
```

## Security

- Verify mod artifact hash before installing.
- Use isolated working directories per job.
- Do not execute arbitrary scripts from mod packages.
- Authenticate uploads with job token.
- Upload logs even on failure.
