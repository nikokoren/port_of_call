import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import YAML from 'yaml';
import {render,engine,layouts} from '../scripts/render.mjs';
const settings=YAML.parse(await readFile('settings.yml','utf8'));
const fixture=JSON.parse(await readFile('fixtures/helsinki.json','utf8'));
const fields=Object.fromEntries(settings.custom_fields.filter(f=>Object.hasOwn(f,'default')).map(f=>[f.keyname,f.default]));
test('all layouts render compact map records identically to legacy markers',async()=>{
 const data=structuredClone(fixture);
 Object.assign(data.vessels[0],{name:'Boat <&"',voyage:'To <Harbor> & coast',bearing_deg:0,speed_knots:0,stale:false,label_rank:0});
 const keys=['mmsi','position','bearing_deg','speed_knots','type','name','length_m','reported_at','stale','label_rank','voyage'];
 const compact={...data,schema_version:2,marker_fields:keys,vessels:data.vessels.map(v=>keys.map(k=>k==='reported_at'?Date.parse(v[k])/1000:v[k]??null))};
 for(const layout of layouts){
  const original=await render(layout,data),packed=await render(layout,compact);
  const markers=html=>[...html.matchAll(/<li\s+data-featured=[^>]+>/g)].map(m=>m[0].replace(/data-reported="[^"]*"/g,''));
  assert.ok(markers(original).length>0,layout+': actual marker markup');
  assert.deepEqual(markers(packed),markers(original),layout);
  assert.ok(packed.includes(`data-reported="${Date.parse(data.vessels[0].reported_at)/1000}"`));
 }
});
test('polling URL sends an optional multi-harbor selection',async()=>{
 const release=JSON.parse(await readFile('deploy/world-release.json','utf8'));
 const base=release.origin+'/api/v1/vessels?harbors=';
 // TRMNL stores a multi-select as a list; join also passes a plain string through.
 for(const [harbor,expected] of [[[],''],[undefined,''],[null,''],[['turku'],'turku'],[['helsinki','rauma'],'helsinki,rauma'],['turku','turku']]){
  const url=await engine.parseAndRender(settings.polling_url,{...fields,harbor});
  assert.equal(url,`${base}${expected}&spotlight=false&format=map`);
 }
 const harbor=settings.custom_fields.find(f=>f.keyname==='harbor');
 assert.equal(harbor.field_type,'select');assert.equal(harbor.multiple,true);assert.equal(harbor.optional,true);
 assert.ok(!Object.hasOwn(harbor,'default'));
 for(const removed of ['map_scale','display_mode'])assert.ok(!settings.custom_fields.some(f=>f.keyname===removed));
 assert.doesNotMatch(settings.polling_url,/scale=/);
 const labels=settings.custom_fields.find(f=>f.keyname==='ship_labels');
 assert.equal(labels.field_type,'boolean');assert.equal(labels.default,false);
 assert.equal(settings.no_screen_padding,'yes');
 assert.ok(settings.description.length<=35,'TRMNL short description must be at most 35 characters');
 assert.equal(settings.framework_version,'3.4.4');assert.equal(settings.refresh_interval,15);
});
for(const layout of layouts)test(`${layout}: boolean ship labels and inset corner`,async()=>{
 for(const [value,expected] of [[true,'on'],['true','on'],['on','on'],[false,'off'],['false','off'],[undefined,'off']])
  assert.ok((await render(layout,fixture,{ship_labels:value})).includes(`data-labels="${expected}"`));
 const html=await render(layout,fixture);
 assert.ok(!html.includes('data-mode'));
 // Fixed harbor zoom: the payload camera drives zoom and centre; legacy payloads fall back to fitting.
 assert.match(html,/data-zoom=""/);assert.ok(html.includes(`data-center="${fixture.port.center.join(',')}"`));
 const fixed=await render(layout,{...fixture,camera:{zoom:11,center:[24.96,60.16]}});
 assert.ok(fixed.includes('data-zoom="11"'));assert.ok(fixed.includes('data-center="24.96,60.16"'));assert.match(html,/class="absolute bottom--3 left--3 right--3 [^"]*poc__corner"/);
});
for(const layout of layouts){
 test(`${layout}: fields, markers, escaping and fallback states`,async()=>{
  const data=structuredClone(fixture);data.port.name='<script>bad()</script>';
  data.vessels[0].name='" onmouseover="bad()';
  data.vessels[0].voyage='To <script>bad()</script> \" onmouseover=\"bad()';
  const html=await render(layout,data,{ship_labels:true});
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

test('TRMNL review: contact, Spotlight clamp, no inline style or opacity, short harbor name',async()=>{
 assert.equal(settings.custom_fields.find(f=>f.keyname==='author_bio').email_address,'isarworks@gmail.com');
 const data=JSON.parse(await readFile('fixtures/rauma-spotlight.json','utf8'));
 data.port={...data.port,name:'Seattle — Elliott Bay',country:'USA'};
 for(const layout of layouts){
  const source=await readFile(layout+'.liquid','utf8');
  assert.doesNotMatch(source,/style="/,layout+': inline style');
  assert.doesNotMatch(source,/opacity/,layout+': opacity');
  const html=await render(layout,data,{port_facts:true});
  assert.match(html,/<span class="w--full title [^"]*" data-clamp="1" data-clamp-lg="2" data-poc-title>/);
  assert.match(html,/class="poc__spotlight poc__spotlight--pending /);
  // A unit never wraps away from its number ("8\nm" on narrow cards).
  assert.ok(html.includes('205&nbsp;m'),layout+': measurement unit kept with value');
  assert.ok(html.includes('Seattle, USA'));assert.ok(!html.includes('Elliott Bay'));
  // Larger count on large screens where the card has room; compact views keep it small.
 if(layout==='full'||layout==='half_vertical')assert.match(html,/label--small lg:label--large" data-poc-count>\d+ vessels/);
 }
 assert.doesNotMatch(await readFile('shared.liquid','utf8'),/opacity/);
});

test('ship markers carry type, speed and length for their icons',async()=>{
 const data=JSON.parse(await readFile('fixtures/rauma-spotlight.json','utf8'));
 data.vessels=data.vessels.slice(0,2);
 Object.assign(data.vessels[0],{type:'cargo',speed_knots:12.5,length_m:229});
 Object.assign(data.vessels[1],{type:null,speed_knots:null});delete data.vessels[1].length_m;
 for(const layout of layouts){
  const html=await render(layout,data);
  assert.match(html,/data-type="cargo" data-speed="12.5" data-length="229"/,layout);
  assert.match(html,/data-type="" data-speed="" data-length=""/,layout+': missing values stay empty');
 }
 const shared=await readFile('shared.liquid','utf8');
 // Motion shows as fill: outlined when stopped, dashed when old; no speed marks.
 assert.match(shared,/poc__ship--stopped path \{ fill:var\(--poc-paper\)/);
 assert.match(shared,/poc__ship--stale path \{[^}]*stroke-dasharray/);
 assert.doesNotMatch(shared,/poc__wake|speedMarks|__pocSpeedStyle/);
 // Ships under way are solid ink; only the Spotlight ship has a paper outline.
 assert.match(shared,/\.poc__ship path \{ fill:currentColor; stroke:currentColor;/);
 assert.match(shared,/\.poc__ship--featured path \{ stroke:var\(--poc-paper\)/);
 // The Spotlight ship keeps the normal size; only its paper outline sets it apart.
 assert.doesNotMatch(shared,/featured\?1\.5/);
 // Spotlight does not restyle or shrink the other ships.
 assert.doesNotMatch(shared,/poc-context|0\.75/);
 // "Port of Call" one step up: always on full; on large screens only elsewhere,
 // since the OG city name in those layouts is the same 16px.
 for(const layout of layouts){
  const source=await readFile(layout+'.liquid','utf8');
  assert.ok(source.includes(layout==='full'?'<span class="label label--base">Port of Call':'<span class="label label--small lg:label--base">Port of Call'),layout);
 }
});

test('Spotlight setting is a native off-by-default boolean',async()=>{
 assert.match(settings.custom_fields.find(f=>f.keyname==='author_bio').description,/Wikidata.*CC0/);
 assert.doesNotMatch(settings.description,/reported/i);
 const field=settings.custom_fields.find(f=>f.keyname==='ship_spotlight');
 assert.equal(field.field_type,'boolean');assert.equal(field.default,false);
 const url=await engine.parseAndRender(settings.polling_url,{...fields,ship_spotlight:true});
 assert.ok(url.endsWith('&spotlight=true&format=map'));
});
for(const layout of layouts)test(`${layout}: ordered ship copy and map-level source credits`,async()=>{
 const data=JSON.parse(await readFile('fixtures/rauma-spotlight.json','utf8'));
 data.focus.name='<script>danger()</script>';
 // Values keep their units on one line (&nbsp;); compare the text as read.
 const html=(await render(layout,data,{ship_labels:false,ship_spotlight:true})).replaceAll('&nbsp;',' ');
 const harbor=html.match(/<aside[^>]*data-poc-box[^>]*>([\s\S]*?)<\/aside>/)[1];
 const overlay=html.match(/<aside[^>]*data-poc-spotlight[^>]*>([\s\S]*?)<\/aside>/)[1];
 assert.ok(harbor.includes('Port of Call'));assert.ok(harbor.includes('Rauma, Finland'));
 assert.ok(harbor.includes('vessels in area'));
 if(layout!=='full')assert.ok(!harbor.includes('vessels seen'));
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
 assert.doesNotMatch(overlay,/\bAIS\b/);
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
 data.focus.presentation.speed='0 knots';html=(await render(layout,data)).replaceAll('&nbsp;',' ');
 assert.ok(html.includes('0 knots'));assert.ok(!html.includes('data-poc-measurements'));
});

for(const layout of layouts)test(`${layout}: port facts are opt-in, escaped and below the count`,async()=>{
 const data=JSON.parse(await readFile('fixtures/rauma-spotlight.json','utf8'));
 data.port_fact={text:'<script>bad()</script>',source_url:'https://example.invalid'};
 const off=await render(layout,data,{port_facts:false});assert.doesNotMatch(off,/<span[^>]* data-poc-port-fact(?:\s|>)/);
 const on=await render(layout,data,{port_facts:true});
 const harbor=on.match(/<aside[^>]*data-poc-box[^>]*>([\s\S]*?)<\/aside>/)[1];
 assert.ok(harbor.includes('&lt;script&gt;bad()&lt;/script&gt;'));
 assert.ok(harbor.indexOf('data-poc-port-fact')>harbor.indexOf('vessels '));
 if(layout==='quadrant'||layout==='half_horizontal')assert.ok(harbor.includes('hidden lg:block'));
 assert.ok(!on.includes('source_url'));
 assert.ok((await render(layout,data,{port_facts:'true'})).includes('data-poc-port-fact'));
});


test('copy-and-paste custom fields match the canonical live settings',async()=>{
 const copied=YAML.parse(await readFile('custom_fields.yml','utf8'));
 assert.deepEqual(copied,settings.custom_fields);
 const live=JSON.parse(await readFile('deploy/release.json','utf8'));
 assert.ok(settings.polling_url.startsWith(live.origin+'/api/v1/vessels?'));
});

test('vessel legend is optional and appears only on full-screen maps',async()=>{
 const field=settings.custom_fields.find(f=>f.keyname==='map_legend');
 assert.equal(field.field_type,'boolean');assert.equal(field.default,false);
 for(const layout of layouts){
  assert.doesNotMatch(await render(layout,fixture),/<aside[^>]*data-poc-legend/);
  for(const value of [true,'true','on',false,'false',undefined]){
   const html=await render(layout,fixture,{map_legend:value});
   const legend=html.match(/<aside[^>]*data-poc-legend[^>]*>([\s\S]*?)<\/aside>/);
   assert.equal(!!legend,layout==='full'&&[true,'true','on'].includes(value));
   if(legend){
    assert.match(legend[0],/class="poc__legend inline-flex/);
    assert.doesNotMatch(legend[0].split('>')[0],/outline|bg--canvas|p--2/);
    for(const shape of ['freighter','passenger','fishing','small','ship'])assert.ok(legend[1].includes(`data-poc-hull="${shape}"`));
    for(const name of ['Cargo/tanker','Passenger','Fishing','Other','Unknown'])assert.ok(legend[1].includes(name));
   }
  }
 }
});

test('harbor landmarks are built in, ignore retired settings and escape their names',async()=>{
 assert.ok(!settings.custom_fields.some(f=>f.keyname==='map_landmarks'));
 const data={...fixture,landmarks:[{name:'<unsafe>',position:[24.9,60.1]}]};
 for(const layout of layouts){
  const on=await render(layout,data);assert.ok(!on.includes('data-landmarks='));assert.ok(on.includes('data-name="&lt;unsafe&gt;"'));
  assert.equal(await render(layout,data,{map_landmarks:false}),on);
  const related=await render(layout,{...data,landmarks:[{...data.landmarks[0],fact_related:true}]});
  assert.match(related,/<li data-related="true" data-lon=/,layout+': current-fact association reaches the native map');
 }
});

test('all four layouts expose the X camera and retain the legacy OG fallback',async()=>{
 const approved=JSON.parse(await readFile('docs/approved-framing.json','utf8')).harbors.seattle;
 const profiles=Object.fromEntries(Object.entries(approved).map(([k,c])=>[k,{zoom:c.zoom,center:c.focus}]));
 for(const layout of layouts){
  const html=await render(layout,{...fixture,camera:{...profiles.og,profiles}});
  assert.ok(html.includes(`data-zoom="${profiles.og.zoom}"`));
  assert.ok(html.includes(`data-zoom-x="${profiles.x.zoom}"`));
  assert.ok(html.includes(`data-center-x="${profiles.x.center.join(',')}"`));
  const legacy=await render(layout,{...fixture,camera:profiles.og});assert.ok(legacy.includes('data-zoom-x=""'));
 }
});
