# Productivity Tools

A collection of small, independent productivity tools. Each tool lives in its own folder under `tools/`, has its own dependencies, and can be used on its own — nothing here depends on anything else in the repo. This root README is just the index so everything is easy to find in one place.

## Tools

| Tool | Description | Status |
|------|-------------|--------|
| _(none yet)_ | | |

Add a row here whenever you add a new tool folder.

## Adding a new tool

1. Copy `tools/_template` to `tools/your-tool-name`.
2. Fill in that folder's `README.md` (purpose, how to run it, dependencies).
3. Add whatever dependency manifest fits the tool (`package.json`, `requirements.txt`, `go.mod`, etc.) — keep it scoped to that folder.
4. Add a row for it in the table above.
5. Commit and push.

## Conventions

- Folder names: `kebab-case` (e.g. `pdf-merge`, `word-counter`).
- Every tool folder has its own `README.md` following the template's skeleton (Purpose / Usage / Status).
- No shared code between tools. If two tools genuinely need to share something, that's a signal it should be its own tool or its own small library — not silently coupled.
- Keep each tool's own dependencies inside its own folder so one tool's setup never affects another's.
