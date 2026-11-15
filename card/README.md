# Weather System — portable scenario lab

A GitHub-ready React + TypeScript + Vite prototype for a hyperlocal adaptive weather app. **Four JSON fixtures render through one shared UI system.** No API keys, external weather service, or backend are needed.

## Quick start

```bash
npm install
npm run dev
```

Open the URL printed by Vite. The default view loads `live.json` (put one next to `index.html`, or open `?lab` to see the four scenarios). In production, rainwatch writes `live.json` every 15 minutes and publishes the card at `/rainwatch/card/`.

```bash
npm test
npm run build
```

## Structure
- `PRODUCT.md` — purpose, principles, scope.
- `DESIGN-SYSTEM.md` — components, hierarchy, visual semantics.
- `DISPLAY-RULES.md` — state/visibility rules, confidence, time handling.
- `DECISIONS.md` — accepted decisions and open questions.
- `AGENTS.md` — cross-AI editing protocol.
- `scenarios/*.json` — canonical test fixtures.
- `src/types.ts` — typed data contract.
- `src/lib/rules.ts` — display rules and fixture validation.
- `src/components/` — shared UI components.
- `src/styles.css` — shared visual styles.

## Work with another AI
Give it this entire repository and ask it to read `AGENTS.md` before making changes. Example: “Improve the 72-hour chart for small screens. Update the shared Timeline component, preserve all four scenarios, run tests, and document any new design decision.”

## Production limitations
All scenario values, critical windows, and confidence labels are illustrative. A future production build needs forecast data, official alert sourcing, calibrated timing confidence, validated driveway flood risk, timezone-aware timestamps, and accessibility testing.
