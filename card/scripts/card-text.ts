/** Print what the live card says, for the archive:  npx vite-node scripts/card-text.ts ../site/live.json */
import { readFileSync } from 'node:fs';
import type { Scenario } from '../src/types';
import { cardText } from '../src/lib/cardtext';

process.stdout.write(JSON.stringify(cardText(JSON.parse(readFileSync(process.argv[2], 'utf8')) as Scenario)) + '\n');
