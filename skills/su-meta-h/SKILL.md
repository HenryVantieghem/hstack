---
name: su-meta-h
description: Set up, inventory, refresh or teach a local skill router, including opt-in specialist visibility changes and reversible scope-specific preferences.
metadata:
  related: "meta-h"
---

# Set up local skill routing

Ask which host and scope the user wants to configure when the request leaves these ambiguous. Inventory is read-only. Use private, user-selected storage for settings and examples. Describe the exact changes to the user before editing host registration or moving files.

| Operation | Action | Completion check |
| --- | --- | --- |
| Inventory | Enumerate the host's advertised skills and any explicitly selected local skill roots. Distinguish host-visible, catalog-only, duplicate and unavailable entries. | Open a selected entry at its actual source and show its name and scope. |
| Setup | Select project or user scope and the local sources the router may consult. Offer to keep existing registrations intact. Record the user's preferences in a supported local configuration or an explicitly chosen local file. | Start a fresh host session if needed and check that its inventory and the router's sources match the chosen setup. |
| Refresh | Read the same approved sources again, compare added, missing and renamed skills, and update derived inventory using the catalog command below where applicable. Preserve user-approved examples and manual choices. | Search for an added or changed specialist and check its current path and description. |
| Learn | Show the proposed example as “when the user asks X in scope Y, prefer skill Z.” Confirm Z is available. A direct instruction naming the phrase, skill and scope authorizes saving that alias immediately. Ask about inferred preferences before saving them. Strip secrets and incidental personal details. | Try the approved wording and one unrelated request against the rule, then report the results. |

If installed alone, this skill can inventory and configure sources by itself. Check whether **meta-h** is installed. If it is missing, explain what routing would add and let the user choose inventory-only setup or separate installation. If the user already requested installation from an identified source, carry out that selection without asking again. Do not invoke either router from within this setup workflow.

## Control specialist visibility

Many hosts advertise skill names and descriptions before loading a selected SKILL.md body. A separate catalog can reduce the number of descriptors only when the host supports limiting what it discovers. The host controls context loading. Verify actual behavior for its version before making a savings claim.

For an opt-in compact setup, identify the host's documented discovery roots or supported registration controls and offer a specific before-and-after inventory. Keep the router discoverable. Leave vendor-managed installs in place and use supported per-skill visibility controls if available. For user-owned specialist directories the user expressly chooses to relocate, choose a private path outside every automatic discovery root and verify the host can read it on demand. Check for package dependencies, broken relative links and other hosts sharing the directory. Preserve each complete directory and a restoration map with original and new locations. Obtain approval for the named paths before changing them. Avoid overwriting either location.

After applying the choice, refresh the catalog and start a fresh session. Verify a relocated specialist is absent from the advertised inventory, remains readable by exact catalog path, and can be used by reading its trusted SKILL.md path on this host. If the check fails, offer to restore the recorded registration or directory and repeat the inventory. When a host cannot support this setup, keep the existing registration and explain the limitation.

## Local catalog

The script lives at `scripts/catalog.py` inside **meta-h**. Run commands from the active project. Substitute the skill's actual installation path for the project path below. If this setup skill is installed alone, use the host's native inventory or the user's selected sources until they choose to install meta-h.

```sh
catalog=.agents/skills/meta-h/scripts/catalog.py
python3 "$catalog" status
python3 "$catalog" sync --root /path/to/approved-specialists
python3 "$catalog" search "inbound phone"
python3 "$catalog" sync --forget-root /path/to/approved-specialists
```

Adding a root persists it across refreshes. Use `sync --forget-root` only when asked to remove that root from future scans. The skill files stay in place. Check `status` after either change. For taught phrases, use the scoped `alias add`, `alias list` and `alias remove` commands. Verify the selected skill's identifier with `show` before adding a rule and search the phrase after the change. The example below assumes the current project and an exact identifier obtained from the catalog. Select another project by placing `--project DIR` before the subcommand.

```sh
python3 "$catalog" alias add "triage my inbound call flow" EXACT_ID
python3 "$catalog" alias list
python3 "$catalog" search "triage my inbound call flow"
```

To undo that example when requested, run `python3 "$catalog" alias remove "triage my inbound call flow"` and check the list again.

**Examples**

- “Inventory the skills available in this project.” Show the available names and sources. Make no changes.
- “Teach the router that ‘triage my inbound call flow’ means voice-agent-us in this project.” Verify the specialist and scope, show the proposed rule and its destination, save the directed alias and confirm it appears in the scoped list.
