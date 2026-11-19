# hstack

Tell your coding agent what you want to get done. **meta-h** finds the right skill or command, reads its instructions and gets to work. **su-meta-h** maintains its private local catalog and remembers the routes you teach it. The first four specialists cover Mac maintenance, client commitments, and business voice agents in the US and EU.

[Watch the routing demo (MP4)](https://github.com/HenryVantieghem/hstack/releases/download/v0.2.0/hstack-routing.mp4) · [Watch the original Mac demo (MP4)](https://github.com/HenryVantieghem/hstack/releases/download/v0.1.0/hstack-launch.mp4)

## Install the router in a project

Start in the project where you use Codex or Claude Code. You need Git, Node with npx, and Python 3.9 or later. The commands below use a personal library directory outside your agent's automatic skill folders. If you already cloned hstack, use that checkout for `library` and skip the clone.

```sh
library="$HOME/.local/share/hstack"
git clone https://github.com/HenryVantieghem/hstack.git "$library"
npx skills add "$library" --skill meta-h su-meta-h --agent claude-code codex -y
python3 .agents/skills/meta-h/scripts/catalog.py sync --root "$library/skills"
```

In a fresh Codex session in that project, ask:

> $meta-h My Mac slowed down before a large build. Check whether I can start it.

Or in Claude Code:

> /meta-h Build a French and Dutch phone receptionist for a Belgian warehouse. Ask me where call data can go.

For a personal shortcut, tell the same router:

> $meta-h In this project, teach the router that “opening shift” means work-chief-of-staff.

Use `$su-meta-h` directly when you want to inspect the catalog, refresh it after installs, or remove a learned route. If no local skill fits, the router turns to **find-skills**. Add it once if your host doesn't already have it:

```sh
npx skills add vercel-labs/skills --skill find-skills --agent claude-code codex -y
python3 .agents/skills/meta-h/scripts/catalog.py sync
```

## What enters the conversation?

The SQLite catalog lives on your machine and is scoped to your project. It indexes skill descriptions, local commands and their relationships. A search returns a shortlist. The router opens one selected file on demand. Learned phrases point to a particular skill in that project. The catalog does not need an account, embedding service or database server.

The install above registers just the two routing skills from hstack with your host. The four bundled specialists stay in the library. Codex and Claude Code can still advertise descriptions for skills already installed in their own discovery folders. Your existing installations and the host's context policy determine those costs. Plugin skills exposed only by a running host can also be selected from its advertised inventory.

To see exactly what the router sees, run these from the project directory:

```sh
catalog=.agents/skills/meta-h/scripts/catalog.py
python3 "$catalog" status
python3 "$catalog" search "Belgian warehouse phone receptionist" --limit 3
```

To open one result, run `python3 "$catalog" show ID` with the exact ID printed by search. An external library remains registered across refreshes. Run `python3 "$catalog" sync --forget-root "$library/skills"` to remove that library from this project's index.

## Skills

| Skill | When to use it |
| --- | --- |
| [meta-h](skills/meta-h/SKILL.md) | Give it a task. It selects an available specialist or command, opens the instructions, and carries the task through. |
| [su-meta-h](skills/su-meta-h/SKILL.md) | Set up the router, add or remove a library, or teach it what a phrase means in a specific project. |
| [mac-maintainer](skills/mac-maintainer/SKILL.md) | Check the actual Mac's disk, memory pressure and build readiness. The read-only snapshot uses stock macOS tools. |
| [work-chief-of-staff](skills/work-chief-of-staff/SKILL.md) | Find promises in a board and meeting notes. Identify the next deliverable, its owner and the decision holding it up. |
| [voice-agent-us](skills/voice-agent-us/SKILL.md) | Build an American after-hours receptionist with Retell. Choose storage, a human fallback, and a test for an unanswered transfer. |
| [voice-agent-eu](skills/voice-agent-eu/SKILL.md) | Build a multilingual European switchboard. Establish where audio, transcripts and model inference can go, then test the carrier and human handoff. |

If you want all six to appear individually in your host's skill picker, run `npx skills add HenryVantieghem/hstack --skill '*' --agent claude-code codex -y` in the project. Direct invocations use `$mac-maintainer` in Codex or `/mac-maintainer` in Claude Code.

## License

[MIT](LICENSE).
