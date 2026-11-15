import { Sun, CloudSun, Cloud, CloudRain, CloudDrizzle, CloudLightning, CloudRainWind, Moon, Sunset } from 'lucide-react';
import type { IconName } from '../types';
const icons = { sun:Sun, 'cloud-sun':CloudSun, cloud:Cloud, 'cloud-rain':CloudRain, 'cloud-drizzle':CloudDrizzle, 'cloud-lightning':CloudLightning, 'cloud-rain-wind':CloudRainWind, moon:Moon, sunset:Sunset };
export function WeatherIcon({name,size=22}:{name:IconName;size?:number}) { const Component=icons[name]; return <Component size={size} strokeWidth={1.7} aria-hidden="true"/>; }
