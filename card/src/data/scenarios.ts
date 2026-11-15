import october from '../../scenarios/october.json';
import rain from '../../scenarios/rain.json';
import storm from '../../scenarios/storm.json';
import heat from '../../scenarios/heat.json';
import type { Scenario } from '../types';
// JSON fixtures are canonical. Runtime validation is performed in the scenario lab.
export const scenarios = [october,rain,storm,heat] as Scenario[];
