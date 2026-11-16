/** Builds a static phone test page for the flood-potential state (v0.19 exploration). Run: npx vite-node tools/potential-test.tsx */
import { readFileSync, writeFileSync } from 'node:fs';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { scenarios } from '../src/data/scenarios';
import { Timeline } from '../src/components/Timeline';
import { WeatherCard } from '../src/components/WeatherCard';

const s = scenarios.find(x => x.id === 'storm-ahead')!;
const css = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');
const noKey = (h: string) => h.replace(/<p class="chart-potential-key">[\s\S]*?<\/p>/, '');
const graph = noKey(renderToStaticMarkup(createElement('article', { className: 'weather-card' }, createElement(Timeline, { scenario: s, potential: 'outline' }))));
const card = renderToStaticMarkup(createElement(WeatherCard, { scenario: s, potential: 'outline' }));
const html = `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rainwatch · quick question</title><style>${css}
body{background:#f2f4f5}.t{max-width:460px;margin:0 auto;padding:18px 12px 48px;font:15px/1.45 -apple-system,BlinkMacSystemFont,Inter,sans-serif;color:#26343d}
.t h1{font-size:20px;margin:6px 0 4px}.t .q{font-size:17px;font-weight:650;margin:18px 4px 6px}.t .hint{color:#7b8991;font-size:13px;margin:0 4px 14px}
.t details{margin-top:22px}.t summary{cursor:pointer;font-weight:650;color:#2f6f95;padding:10px 4px}.t .note{font-size:12px;color:#86939a;margin:26px 4px 0}
.t .weather-card{margin-top:8px}.t article>section:first-child{border-top:0;padding-top:0}</style></head><body><main class="t">
<h1>A weather graph for this Wednesday</h1>
<p class="hint">Look at the graph for a few seconds. No key on purpose.</p>
${graph}
<p class="q">What do you think the striped boxes above the Wednesday bars mean? Would you do anything about them?</p>
<p class="hint">Answer out loud before opening the next part.</p>
<details><summary>Show the whole card, with its key</summary>${card}
<p class="q">Now: does the striped area mean you should put out sandbags?</p></details>
<p class="note">Rainwatch lab test, flood potential (illustrative, based on the forecast of Mon Nov 16, 8 AM). Not a forecast to act on.</p>
</main></body></html>`;
writeFileSync('/tmp/shots/potential-test.html', html);
console.log('wrote', html.length);
