// Compare two candidate limits from identical genuine archived observations.
// Only the preview subset changes; map camera and source positions do not.
import assert from 'node:assert/strict';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {chromium} from 'playwright';
import {geometry} from './visual-geometry.mjs';
import {previewPixels} from './preview-pixels.mjs';

const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH,
 args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const cases=[
 ['og','full','og',false],['x','full','x',false],['portrait','full','portrait',false],
 ['half-horizontal','half_horizontal','og',false],['half-vertical','half_vertical','og',false],
 ['quadrant','quadrant','og',false],['portrait-quadrant','quadrant','portrait',false],
 ['spotlight','full','og',true],['spotlight-x','full','x',true],
 ['spotlight-dark','full','og',true,true]
];
const results=[];
await mkdir('docs/screenshots',{recursive:true});
try {
 for(const [name,layout,device,focus,dark=false] of cases){
  const fixture=focus?'seattle-candidates-spotlight':'seattle-candidates';
  const source=JSON.parse(await readFile('fixtures/'+fixture+'.json','utf8'));
  assert.equal(source.demo,false);assert.equal(source.schema_version,2);
  assert.ok(source.vessels.length>40,'Comparison needs more than 40 actual candidates');
  let previous;
  for(const candidates of [40,80]){
   const big=device==='x'||device==='portrait';
   const page=await browser.newPage({viewport:{width:device==='portrait'?780:big?1040:800,
    // The native X framework already scales 1040x780 to 1872x1404.
    // A second 1.8 DPR would oversample the exported screenshot again.
    height:device==='portrait'?1040:big?780:480},deviceScaleFactor:1});
   const errors=[];page.on('pageerror',e=>errors.push(e.message));
   if(process.env.MAP_RELAY==='true')await page.route(/^https:\/\/(maps\.trmnl\.com|trmnl\.com|usetrmnl\.com)\//,async route=>{
    try{const r=await fetch('http://127.0.0.1:8788/?url='+encodeURIComponent(route.request().url()));
     await route.fulfill({status:r.status,body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'application/octet-stream'});
    }catch{await route.abort();}
   });
   await page.goto(`http://127.0.0.1:8787/?fixture=${fixture}&layout=${layout}&device=${device}&candidates=${candidates}&labels=on&facts=true&legend=true&dark=${dark}`);
   await page.waitForFunction(()=>document.querySelector('.poc')?.dataset.mapReady==='true',{timeout:35000});
   await page.evaluate(()=>document.fonts.ready);
   await page.waitForFunction(()=>window.TRMNL_PLUGINS_READY===true,{timeout:25000});
   const g=await page.evaluate(geometry);
   const state=await page.evaluate(()=>{
    const root=document.querySelector('.poc'),map=root.__portOfCallMap;
    return {camera:{center:map.getCenter().toArray(),zoom:map.getZoom()},
     count:root.querySelector('[data-poc-count]').textContent,
     candidates:[...root.querySelectorAll('.poc__data li')].map(n=>({id:n.dataset.id,
      position:[Number(n.dataset.lon),Number(n.dataset.lat)],reported:Number(n.dataset.reported)})),
     visible:[...root.querySelectorAll('.poc__ship')].map(n=>n.dataset.id)};
   });
   assert.deepEqual(errors,[]);
   for(const key of ['mapCountMatches','countSuffixTogether','countDividerSpaced','cardAtCorner','cardInside',
    'landmarksClear','landmarkPinsExact','labelContentsValid','spotlightInside','spotlightClear',
    'spotlightConnected','spotlightInverted','spotlightTextConsistent','spotlightTextVisible',
    'attributionInside','attributionClear','attributionTight','legendInside','legendClear','legendCompact'])
    assert.equal(g[key],true,name+' '+candidates+' '+key);
   for(const key of ['labelCollisions','leaderCollisions','labelsOutside','hiddenShips','textOverflow'])
    assert.equal(g[key],0,name+' '+candidates+' '+key);
   assert.ok(g.maxProjectionError<1,'Hull anchors stay on actual geographic coordinates');
   const originals=new Map(source.vessels.map(row=>[row[0],row]));
   for(const v of state.candidates){
    const original=originals.get(v.id);assert.deepEqual(v.position,original[1]);assert.equal(v.reported,original[7]);
   }
   if(previous){
    assert.deepEqual(state.camera,previous.camera,'Density must not move or zoom the map');
    assert.deepEqual(state.candidates.slice(0,40),previous.candidates,'Same first 40 source observations');
   }
   previous=state;
   const file=`candidates-${name}-${candidates}`;
   const pixels=previewPixels(await page.locator('.screen').screenshot({path:`docs/screenshots/${file}.png`}));
   const cssWidth=device==='portrait'?780:big?1040:800,cssHeight=device==='portrait'?1040:big?780:480;
   const scale=big?1.8:1;
   assert.equal(pixels.width,Math.round(cssWidth*scale/(['half_vertical','quadrant'].includes(layout)?2:1)));
   assert.equal(pixels.height,Math.round(cssHeight*scale/(['half_horizontal','quadrant'].includes(layout)?2:1)));
   results.push({name:file,layout,device,spotlight:focus,dark,source:fixture,snapshot_at:source.snapshot_at,
    source_bytes:Buffer.byteLength(JSON.stringify(source)),limit:candidates,...state,geometry:g,pixels,errors});
   console.log(file,state.count,g.labels+' labels');await page.close();
  }
 }
 await writeFile('docs/screenshots/results-candidates.json',JSON.stringify(results,null,2)+'\n');
}finally{await browser.close();}
