import {chromium} from 'playwright';
import {geometry} from './visual-geometry.mjs';
import {previewPixels} from './preview-pixels.mjs';
import {writeFile} from 'node:fs/promises';
const browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const cases=[['og-mashup-quadrants','quadrant','og',4,800,480],['x-mashup-halves','half_vertical','x',2,1872,1404],['spotlight-mashup-quadrants','quadrant','og',4,800,480,'rauma-spotlight'],['spotlight-mashup-halves','half_vertical','x',2,1872,1404,'turku-spotlight']];
const results=[];
try{
 for(const [name,layout,device,copies,width,height,fixture='helsinki'] of cases){
  const page=await browser.newPage({viewport:{width,height}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  if(process.env.MAP_RELAY==='true')await page.route(/^https:\/\/(maps\.trmnl\.com|trmnl\.com|usetrmnl\.com)\//,async route=>{
   const r=await fetch('http://127.0.0.1:8788/?url='+encodeURIComponent(route.request().url()));
   await route.fulfill({status:r.status,body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'application/octet-stream'});
  });
  await page.goto(`http://127.0.0.1:8787/?layout=${layout}&device=${device}&labels=${fixture.endsWith('-spotlight')?'off':'on'}&mashup=true&fixture=${fixture}`);
  await page.waitForFunction(n=>document.querySelectorAll('.poc[data-map-ready="true"]').length===n,copies,{timeout:35000});
  await page.waitForFunction(()=>window.TRMNL_PLUGINS_READY===true,{timeout:25000});
  const positions=await page.evaluate(`[...document.querySelectorAll('.poc')].map(${geometry.toString()})`);
  if(errors.length||positions.length!==copies||positions.some(p=>!p.spotlightTextConsistent||!p.spotlightInverted||!p.spotlightTextVisible||!p.spotlightInside||!p.spotlightClear||!p.spotlightConnected||!p.cardInside||!p.cardAtCorner||!p.attributionInside||!p.attributionClear||p.hiddenShips||p.maxProjectionError>1||p.labelCollisions||p.leaderCollisions||p.labelsOutside||p.textOverflow))throw new Error(name+': '+JSON.stringify({positions,errors}));
  const isolated=await page.evaluate(()=>{
   const maps=[...document.querySelectorAll('.poc')].map(e=>e.__portOfCallMap);
   return new Set(maps).size===maps.length && [...document.querySelectorAll('.poc')].every(e=>e.querySelectorAll('.poc__ship').length>0);
  });
  if(fixture.endsWith('-spotlight')){
   const featured=await page.evaluate(()=>[...document.querySelectorAll('.poc')].every(el=>el.querySelector('.poc__ship--featured')&&el.querySelector('[data-poc-spotlight][data-id="'+el.dataset.focus+'"]')));
   if(!featured)throw new Error(name+': missing featured marker/name');
  }
  if(!isolated)throw new Error(name+': missing or shared map state');
  const pixels=previewPixels(await page.locator('.screen').screenshot({path:`docs/screenshots/${name}.png`}));
  results.push({name,copies,positions,isolated,pixels,errors});console.log(name,copies,'independent maps passed');await page.close();
 }
 await writeFile('docs/screenshots/results-mashups.json',JSON.stringify(results,null,2)+'\n');
}finally{await browser.close();}
