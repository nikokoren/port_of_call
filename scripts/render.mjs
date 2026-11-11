import { Liquid } from 'liquidjs';
import { readFile } from 'node:fs/promises';
export const layouts=['full','half_horizontal','half_vertical','quadrant'];
export const engine=new Liquid();
export async function render(layout,data,fields={}) {
  if(!layouts.includes(layout))throw new Error('Invalid layout');
  const trmnl={plugin_settings:{custom_fields_values:{harbor:[],ship_labels:false,ship_spotlight:false,port_facts:false,map_legend:false,...fields}}};
  return engine.parseAndRender(await readFile('shared.liquid','utf8')+await readFile(layout+'.liquid','utf8'),{...data,trmnl});
}
