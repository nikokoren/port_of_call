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
 assert.equal(settings.framework_version,'3.4.4');assert.equal(settings.refresh_interval,15);
 assert.deepEqual(settings.custom_fields.find(f=>f.keyname==='display_mode').options,[{'Harbor Map':'map'}]);
});
for(const layout of layouts){
 test(`${layout}: fields, markers, escaping and fallback states`,async()=>{
  const data=structuredClone(fixture);data.port.name='<script>bad()</script>';
  data.vessels[0].name='" onmouseover="bad()';
  const html=await render(layout,data,{ship_labels:'on'});
  assert.ok(html.includes('data-labels="on"'));assert.ok(html.includes('&lt;script&gt;'));
  assert.match(html,/(&quot;|&#34;) onmouseover=(&quot;|&#34;)/);assert.ok(!html.includes('<script>bad()'));
  assert.ok(html.includes('data-poc-box'));assert.ok(!html.includes('poc__header'));
  assert.ok(html.includes('data-bearing='));assert.ok(html.includes('CC BY 4.0'));
  for(const state of ['empty','stale','unavailable','warming']){
   const h=await render(layout,{...fixture,status:state,message:'STATE MESSAGE',vessels:[]});
   assert.match(h,/class="[^"]*poc__notice"[^>]*>STATE MESSAGE/);
  }
  const missing=await render(layout,{});assert.match(missing,/Vessel feed unavailable/);
  const demo=await render(layout,{...fixture,demo:true});assert.match(demo,/DEMO · SYNTHETIC/);
 });
}

test('Spotlight setting is a native off-by-default boolean',async()=>{
 const field=settings.custom_fields.find(f=>f.keyname==='ship_spotlight');
 assert.equal(field.field_type,'boolean');assert.equal(field.default,false);
 const url=await engine.parseAndRender(settings.polling_url,{...fields,ship_spotlight:true});
 assert.ok(url.endsWith('&spotlight=true'));
});
for(const layout of layouts)test(`${layout}: Spotlight card, reserved subject and honest origin`,async()=>{
 const data=JSON.parse(await readFile('fixtures/rauma-spotlight.json','utf8'));
 data.focus.name='<script>danger()</script>';
 const html=await render(layout,data,{ship_labels:'off',ship_spotlight:true});
 assert.ok(html.includes('Ship Spotlight'));assert.ok(html.includes('&lt;script&gt;'));
 assert.ok(html.includes('data-featured="true"'));assert.ok(!html.includes('<script>danger()'));
 assert.ok(html.includes('Reported to'));assert.ok(html.includes('Position '));
 if(layout==='full'){
  assert.ok(html.includes('Reported from'));assert.ok(html.includes('Wikidata'));assert.ok(html.includes('CC0'));
  data.focus.origin=null;assert.ok((await render(layout,data)).includes('Previous port unknown'));
 }
 data.focus=null;data.focus_message='No suitable fresh ship · showing harbor';
 assert.ok((await render(layout,data)).includes(data.focus_message));
});
