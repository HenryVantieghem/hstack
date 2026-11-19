# hstack

Four agent skills from Henry Vantieghem for the work around shipping software: keeping a Mac ready to build, keeping promises to clients, and getting a business voice agent through its first useful call.

[Watch the 58-second launch film (MP4)](https://github.com/HenryVantieghem/hstack/releases/download/v0.1.0/hstack-launch.mp4)

## Start with your Mac

From the project where you want to use the skill, run:

```sh
npx skills add HenryVantieghem/hstack --skill mac-maintainer --agent claude-code codex -y
```

Start a fresh Claude Code or Codex session in that project and ask:

> Use mac-maintainer. I’m about to start a large build. Check this Mac and tell me whether I should start now and why.

You get a read-only check of the machine you’re actually using. If the evidence points to a problem, the skill explains what to inspect next. The Mac check runs locally with system tools and needs no vendor account.

## Pick a skill

| Skill | Try asking |
| --- | --- |
| [mac-maintainer](skills/mac-maintainer/SKILL.md) | “My build slowed down. Check disk space and memory pressure before I restart anything.” |
| [work-chief-of-staff](skills/work-chief-of-staff/SKILL.md) | “Using this project board and these meeting notes, what did I promise, what’s due first, and which decision needs me?” |
| [voice-agent-us](skills/voice-agent-us/SKILL.md) | “Build an after-hours receptionist for a US HVAC company using Retell. Ask me where call data belongs, then test what happens when dispatch doesn’t pick up.” |
| [voice-agent-eu](skills/voice-agent-eu/SKILL.md) | “Build a French and Dutch dispatch line for a Belgian warehouse. Ask whether EU storage is enough or whether speech and model processing must also stay in the EU.” |

To install all four into your current project:

```sh
npx skills add HenryVantieghem/hstack --skill '*' --agent claude-code codex -y
```

In Claude Code, select a skill with `/mac-maintainer`. In Codex, use `$mac-maintainer`. Substitute any installed skill name from the table. Install the Mac skill on macOS. The other three can be used from any supported development machine.

## What the voice skills ask first

“Where should we store the data?” is really several questions. A warehouse might allow a dispatch ticket in its CRM, want the recording discarded, and require every word spoken on the call to be processed in Europe. Those choices change the phone carrier, speech service, model, logs and fallback route. Start with a fictional caller and a test number. Prove a human can receive the handoff and that the promised record exists before connecting a business line.

## License

[MIT](LICENSE). Use these in your own projects or adapt them for your team.
