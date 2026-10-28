# trex-local-marketplace

A Claude Code plugin marketplace. Each plugin lives in its own folder under `plugins/`.

## Plugins

- [daily-brief](plugins/daily-brief/README.md): a daily personal-assistant brief rendered as one local page.

## Adding a plugin

1. Create `plugins/<name>/` with `.claude-plugin/plugin.json` and the plugin's `skills/`, `commands/`, `agents/` or `hooks/`.
2. Add an entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<name>"`.
3. Add a one-line entry to the list above.

Anything a plugin needs at run time, including scripts and reference files, stays inside its own folder, so a plugin never reaches into another plugin or the repo root.
