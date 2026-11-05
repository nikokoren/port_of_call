import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import YAML from 'yaml';
import {render,engine,layouts} from '../scripts/render.mjs';
const settings=YAML.parse(await readFile('settings.yml','utf8'));
const fixture=JSON.parse(await readFile('fixtures/helsinki.json','utf8'));
const fields=Object.fromEntries(settings.custom_fields.filter(f=>Object.hasOwn(f,'default')).map(f=>[f.keyname,f.default]));
test('polling URL interpolates every harbor and framing value',async()=>{
 for(const harbor of ['helsinki','turku','rauma'])for(const map_scale of ['closer','standard','wider']){
  const url=await engine.parseAndRender(settings.polling_url,{...fields,harbor,map_scale});
  assert.equal(url,`https://YOUR-BACKEND.example/api/v1/harbors/${harbor}/vessels?scale=${map_scale}&spotlight=false`);
 }
 assert.ok(settings.description.length<=35,'TRMNL short description must be at most 35 characters');
 assert.equal(settings.framework_version,'3.4.4');assert.equal(settings.refresh_interval,15);
 assert.deepEqual(settings.custom_fields.find(f=>f.keyname==='display_mode').options,[{'Harbor Map':'map'}]);
});
for(const layout of layouts){
 test(`${layout}: fields, markers, escaping and fallback states`,async()=>{
  const data=structuredClone(fixture);data.port.name='<script>bad()</script>';
  data.vessels[0].name='" onmouseover="bad()';
  data.vessels[0].voyage='To <script>bad()</script> \" onmouseover=\"bad()';
  const html=await render(layout,data,{ship_labels:'on'});
  assert.ok(html.includes('data-labels="on"'));assert.ok(html.includes('&lt;script&gt;'));
  assert.match(html,/(&quot;|&#34;) onmouseover=(&quot;|&#34;)/);assert.ok(!html.includes('<script>bad()'));
  assert.ok(html.includes('data-poc-box'));assert.ok(!html.includes('poc__header'));
  assert.ok(html.includes('data-voyage="To &lt;script&gt;'));assert.ok(html.includes('data-bearing='));assert.ok(html.includes('CC BY 4.0'));
  for(const state of ['empty','stale','unavailable','warming']){
   const h=await render(layout,{...fixture,status:state,message:'STATE MESSAGE',vessels:[]});
   assert.match(h,/class="[^"]*poc__notice"[^>]*>STATE MESSAGE/);
  }
  const missing=await render(layout,{});assert.match(missing,/Vessel feed unavailable/);
  const demo=await render(layout,{...fixture,demo:true});assert.match(demo,/DEMO · SYNTHETIC/);
 });
}

test('Spotlight setting is a native off-by-default boolean',async()=>{
 assert.match(settings.custom_fields.find(f=>f.keyname==='author_bio').description,/Wikidata.*CC0/);
 assert.doesNotMatch(settings.description,/reported/i);
 const field=settings.custom_fields.find(f=>f.keyname==='ship_spotlight');
 assert.equal(field.field_type,'boolean');assert.equal(field.default,false);
 const url=await engine.parseAndRender(settings.polling_url,{...fields,ship_spotlight:true});
 assert.ok(url.endsWith('&spotlight=true'));
});
for(const layout of layouts)test(`${layout}: ordered ship copy and map-level source credits`,async()=>{
 const data=JSON.parse(await readFile('fixtures/rauma-spotlight.json','utf8'));
 data.focus.name='<script>danger()</script>';
 const html=await render(layout,data,{ship_labels:'off',ship_spotlight:true});
 const harbor=html.match(/<aside[^>]*data-poc-box[^>]*>([\s\S]*?)<\/aside>/)[1];
 const overlay=html.match(/<aside[^>]*data-poc-spotlight[^>]*>([\s\S]*?)<\/aside>/)[1];
 assert.ok(harbor.includes('Port of Call'));assert.ok(harbor.includes('Rauma, Finland'));
 assert.ok(harbor.includes('vessels seen near this port'));
 for(const removed of ['Archive','Fetched','Updated','Report ','CC BY','Fintraffic'])assert.ok(!harbor.includes(removed));
 assert.ok(html.includes('map__attribution'));assert.ok(html.includes('data-poc-sources'));assert.ok(html.includes('CC BY 4.0'));assert.ok(html.includes('OpenStreetMap'));
 assert.ok(overlay.includes('&lt;script&gt;'));assert.ok(!overlay.includes('<script>danger()'));
 assert.ok(overlay.includes('Cargo vessel'));assert.ok(!overlay.includes('Type:'));
 const positions=['Cargo vessel','Flag: Netherlands','Voyage:','ETA:','Current speed:'].map(t=>overlay.indexOf(t));
 assert.ok(positions.every(n=>n>=0));assert.deepEqual(positions,[...positions].sort((a,b)=>a-b));
 assert.ok(overlay.includes('Hanko, Finland → Tilbury, United Kingdom'));
 assert.ok(overlay.includes('205 m'));assert.ok(overlay.includes('0 knots'));
 if(layout==='full'||layout==='half_vertical'){
  assert.ok(overlay.indexOf('Good to know')>overlay.indexOf('Current speed:'));
  assert.ok(overlay.indexOf('Ship details')>overlay.indexOf('Good to know'));
  assert.ok(overlay.indexOf('Length')>overlay.indexOf('Shipyard country'));
 }
 assert.ok(!overlay.includes('Position '));
 assert.doesNotMatch(overlay,/reported|draught/i);
 assert.doesNotMatch(harbor,/reported/i);
 assert.doesNotMatch(html,/Wikidata|CC0/);
 data.focus=null;data.focus_message='No suitable fresh ship · showing harbor';
 assert.ok((await render(layout,data)).includes(data.focus_message));
});
for(const layout of layouts)test(`${layout}: absent measurements do not become empty facts`,async()=>{
 const data=JSON.parse(await readFile('fixtures/rauma-spotlight.json','utf8'));
 data.focus.presentation.measurements=[];data.focus.presentation.details=[];data.focus.presentation.speed=null;
 let html=await render(layout,data);
 let overlay=html.match(/<aside[^>]*data-poc-spotlight[^>]*>([\s\S]*?)<\/aside>/)[1];
 assert.ok(!overlay.includes('data-poc-measurements'));assert.ok(!overlay.includes('Current speed:'));
 data.focus.presentation.speed='0 knots';html=await render(layout,data);
 assert.ok(html.includes('0 knots'));assert.ok(!html.includes('data-poc-measurements'));
});
