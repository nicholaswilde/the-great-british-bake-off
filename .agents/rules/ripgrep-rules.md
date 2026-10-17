# Ripgrep (`rg`) Pattern Searching

## Rule
Always use `rg` (prefixed with `rtk rg` in the shell) for searching file contents, code patterns, strings, and regular expressions across the repository.

## Guidelines
1. **RTK Integration**: Always prefix with `rtk` (e.g., `rtk rg <pattern>`) to compress output and filter noise before it reaches the model context.
2. **File Type Filtering**: Use `-t` / `--type` to scope searches (e.g., `rtk rg -t py "class Season"`).
3. **Targeted Scoping**: Scope searches to relevant directories (`src/`, `tests/`, `data/`) rather than unconstrained searches across large binary or cache directories.
4. **Files-Only Listing**: When looking for files containing a pattern, use `-l` / `--files-with-matches` to keep output minimal.
5. **Context Control**: Keep context lines small (`-C 1` or `-C 2`) when examining surrounding lines.

## Common Command Reference
- `rtk rg "pattern" src/` — Search within source directory
- `rtk rg -t py "def scrape" src/` — Search Python definitions
- `rtk rg -i "amazing race"` — Case-insensitive search
- `rtk rg -l "Pydantic"` — List files containing pattern
- `rtk rg -w "Season"` — Match whole word only
