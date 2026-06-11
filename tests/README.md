# tests/

Automated tests live here.

Stack-agnostic layout. Suggested organization:

- Mirror `src/` so each module's tests are easy to locate.
- Separate test types by folder when useful: `unit/`, `integration/`, `e2e/`.
- Keep fixtures and helpers in `tests/fixtures/` or `tests/helpers/`.
- Never commit real credentials in fixtures. Use values from `.env.example` style placeholders.

Test runner, naming convention, and coverage targets are stack-specific —
document them in the project's `CLAUDE.md` and `AGENTS.md`.
