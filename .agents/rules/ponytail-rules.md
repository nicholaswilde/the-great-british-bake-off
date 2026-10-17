# Ponytail (Lazy Senior Dev Mode)

## Rule
Apply the minimalist "lazy senior dev" approach to reduce code bloat, avoid over-engineering, and keep token costs low:

1. **YAGNI (You Aren't Gonna Need It):** Question if code or features need to exist at all.
2. **Reuse Existing Code:** Check for existing helpers, utilities, and patterns in the repository before writing new ones.
3. **Stdlib & Platform First:** Prefer native language features and standard libraries over adding new dependencies.
4. **Minimal Diff:** Aim for the shortest working diff. Deletion over addition. Boring over clever. Fewest files touched.
5. **Mark Deliberate Simplifications:** Use `// ponytail: [reason] -> [upgrade path]` (or `# ponytail:` in Python) comments when intentionally deferring complexity.
