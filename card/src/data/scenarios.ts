import october from '../../scenarios/october.json';
import rain from '../../scenarios/rain.json';
import storm from '../../scenarios/storm.json';
import heat from '../../scenarios/heat.json';
import rainSoon from '../../scenarios/rain-soon.json';
import incomplete from '../../scenarios/incomplete.json';
import upcoming from '../../scenarios/upcoming.json';
import type { Scenario } from '../types';
// JSON fixtures are canonical. Runtime validation is performed in the scenario lab.
export const scenarios = [october,rain,rainSoon,storm,heat,incomplete,upcoming] as Scenario[];
