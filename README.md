# skills

Reusable agent skills.

## Polygon

[polygon](polygon/) supports authoring, testing, stress testing, committing and packaging Codeforces Polygon problems through the official API.

Requires Python 3.9 or newer and network access to Polygon. The Python client uses only the standard library.

### Install

Ask Codex to install the skill from this folder.

```text
Install this skill from https://github.com/Khoray/skills/tree/main/polygon
```

For a local Codex installation, copy the complete `polygon` folder to `~/.agents/skills/polygon` or your project's `.agents/skills/polygon`.

### Configure

Generate the credential file inside the installed skill folder.

```bash
python3 /path/to/polygon/scripts/polygon.py --init-env
```

Edit `/path/to/polygon/.env` and fill in your own API credentials from Polygon Settings.

```dotenv
POLYGON_API_KEY=
POLYGON_API_SECRET=
POLYGON_PIN=
```

`POLYGON_PIN` is optional. The `.env` file is ignored by Git. Keep credential values private.

### Use

Ask Codex to use `$polygon`, or run the client directly.

```bash
python3 /path/to/polygon/scripts/polygon.py problems.list
```

See [SKILL.md](polygon/SKILL.md) and the [API reference](polygon/references/tools.md) for the complete workflow and command examples.
