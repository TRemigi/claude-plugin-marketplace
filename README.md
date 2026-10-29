# trex-local-marketplace

A Claude Code plugin marketplace. Each plugin lives in its own folder under `plugins/`.

## Plugins

- [daily-brief](plugins/daily-brief/README.md): a daily personal-assistant brief rendered as one local page.
- [functional-style](plugins/functional-style/skills/functional-style/SKILL.md): immutability, pure functions and declarative transforms.
- [stratified-design](plugins/stratified-design/skills/stratified-design/SKILL.md): stratified design and the Single Level of Abstraction Principle.
- [herdr](plugins/herdr/skills/herdr/SKILL.md): control the Herdr terminal multiplexer for coding agents.
- [literal-explanations](plugins/literal-explanations/skills/literal-explanations/SKILL.md): explanations that need no prior codebase or domain knowledge.

## Adding a plugin

1. Create `plugins/<name>/` with `.claude-plugin/plugin.json` and the plugin's `skills/`, `commands/`, `agents/` or `hooks/`.
2. Add an entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<name>"`.
3. Add a one-line entry to the list above.

Anything a plugin needs at run time, including scripts and reference files, stays inside its own folder, so a plugin never reaches into another plugin or the repo root.
