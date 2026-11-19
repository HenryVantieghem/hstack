---
name: mac-maintainer
description: Diagnose a slow Mac, check disk and memory headroom, or assess whether the Mac is ready for a large local job.
---

# Mac maintainer

Run `scripts/snapshot.sh` from this skill directory on the Mac being checked. It uses stock macOS tools and reports startup storage, CPU, memory and swap. The report omits process names, arguments, PIDs, usernames and machine names. If the current shell runs elsewhere, state where the check can run and which measurements are missing.

Use the symptom to choose the next observation.

- **Storage.** Compare available GiB with the operation’s expected peak, including temporary files and output. Keep a margin for swap and other jobs. If a large job uses another volume, check that volume too.
- **CPU.** Look at the interval sample and the 1-, 5- and 15-minute load together. Repeat during the slowdown to tell a spike from sustained contention. Process CPU estimates can exceed 100% across cores.
- **Memory.** Use Activity Monitor’s Memory Pressure graph when available. A single free-memory estimate or swap reading gives context. Persistent pressure during the symptom and rising swap are stronger evidence. Resident-memory ranks are per process and can include shared pages.
- **Process attribution.** If useful, ask the user to sort the relevant Activity Monitor view by CPU or Memory, or inspect it locally when access is available. The numeric CPU and memory rankings in the snapshot are independent.

Lead with the strongest observed constraint and the measurements behind it. Give one next check when the cause is uncertain. The snapshot and initial triage are read-only. Any cleanup or process change has its own scope and should be verified with another snapshot and the affected workload.

[Apple’s guide to memory pressure](https://support.apple.com/guide/activity-monitor/check-if-your-mac-needs-more-ram-actmntr34865/mac)
