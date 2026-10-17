# CodeGraph Knowledge Graph Integration

## Rule
Always prioritize using the `codegraph_explore` MCP tool instead of executing multi-turn `grep`/`find`/`read` loops across files when exploring codebase architecture, symbol definitions, caller/callee paths, or blast radius.

## Key Benefits
- **Single Roundtrip:** Retrieves verbatim line-numbered source for relevant symbols, caller/callee call paths, and impact summaries in a single compact response.
- **Token Efficiency:** Prevents dumping full file contents or repetitive search results into agent context.

## CLI Commands
- Check index status: `codegraph status`
- Sync changes after editing files: `codegraph sync`
- Rebuild full index: `codegraph index`
