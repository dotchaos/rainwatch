# Instructions for AI collaborators

Before editing, read `PRODUCT.md`, `DESIGN-SYSTEM.md`, `DISPLAY-RULES.md`, `DECISIONS.md`, and `src/types.ts`.

## Non-negotiable constraints
- Treat this as one adaptive design system, not four separate screens.
- Modify shared components/rules for shared behavior; edit JSON only to change scenario facts.
- Preserve all four fixtures and validate them after every substantive change.
- Keep illustrative forecasts explicitly labeled as illustrative.
- Do not claim validated timing confidence, official warnings, or property-specific flood prediction from the current fixture data.
- Do not use transparency to communicate uncertainty in a way that changes perceived severity.
- Do not use danger red for routine weather icons.
- Live weather enters only through `live.json`, built by `rainwatch/card.py` in the parent repo (accepted v0.4). Don't add other live sources or a location lookup silently.
- The live card must pass the same rules as the fixtures (`src/lib/live.test.ts` runs on every update).

## Change handoff
When proposing or implementing an edit, report: (a) affected files, (b) shared behavior changed, (c) effect on all four scenarios, (d) tests run, (e) remaining concerns. Update `DECISIONS.md` when a decision is accepted.
