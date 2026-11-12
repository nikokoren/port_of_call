import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {readFile,writeFile} from 'node:fs/promises';
const origin=process.env.FRAMING_ORIGIN||'http://127.0.0.1:8890/framing/';
const registry=await readFile('port_of_call/harbors.json','utf8');
const catalog=JSON.parse(await readFile('site/framing/data.json','utf8'));
assert.equal(Object.values(catalog.landmarks).flat().length,97);
const browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage({viewport:{width:1500,height:1100}}),errors=[],failed=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&new URL(r.url()).origin===new URL(origin).origin)failed.push([r.status(),r.url()]);});
 if(process.env.MAP_RELAY==='true')await page.route(/^https:\/\/(maps\.trmnl\.com|trmnl\.com|usetrmnl\.com)\//,async route=>{
  const r=await fetch('http://127.0.0.1:8788/?url='+encodeURIComponent(route.request().url()));await route.fulfill({status:r.status,body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'application/octet-stream'});
 });
 const ready=async()=>{await page.waitForFunction(()=>document.querySelector('#message').textContent.startsWith('Drag to pan'),{timeout:60000});await page.waitForFunction(()=>[...document.querySelectorAll('.poi span')].every(n=>!n.textContent.includes('Loading')));};
 const state=()=>page.evaluate(()=>JSON.parse(document.querySelector('#export').value));
 const frame=()=>page.frames().find(f=>f.url()==='about:srcdoc');
 await page.goto(origin);await ready();assert.equal(await page.locator('#harbor option').count(),16);assert.equal(await page.locator('.poi').count(),5);
 assert.deepEqual((await state()).harbors,{});
 assert.ok((await frame().locator('[data-editor-count]').textContent()).includes('Map framing preview'));
 const nativeOptions=await frame().evaluate(()=>[10.5,11.25].map(zoom=>TRMNLMaps.options({el:document.querySelector('.poc'),preset:'outline',zoom}).zoom));assert.deepEqual(nativeOptions,[11,11]);
 await page.locator('#fractional').check();await page.locator('#zoom').fill('11,25');await page.locator('#zoom').press('Tab');
 await page.waitForFunction(()=>JSON.parse(document.querySelector('#export').value).harbors.seattle?.og?.zoom===11.25);
 await page.locator('#zoom').fill('10.5');await page.locator('#zoom').press('Tab');
 await page.waitForFunction(()=>JSON.parse(document.querySelector('#export').value).harbors.seattle?.og?.zoom===10.5);
 const halfZoom=await frame().evaluate(async()=>{const m=document.querySelector('.poc').__portOfCallMap;await TRMNLMaps.ready(m);return m.getZoom();});assert.equal(halfZoom,10.5);
 await page.locator('#zoom').fill('11.25');await page.locator('#zoom').press('Tab');
 await page.waitForFunction(()=>JSON.parse(document.querySelector('#export').value).harbors.seattle?.og?.zoom===11.25);
 const fractional=await frame().evaluate(async()=>{const map=document.querySelector('.poc').__portOfCallMap;await TRMNLMaps.ready(map);return map.getZoom();});assert.equal(fractional,11.25);
 await page.reload();await ready();assert.equal(await page.locator('#zoom').inputValue(),'11.25');
 // Real pointer drag through the scaled iframe: preserve a harbor anchor, not
 // the port-card-offset visible map center.
 const canvas=await frame().locator('.maplibregl-canvas').boundingBox(),before=(await state()).harbors.seattle.og.focus;
 await page.mouse.move(canvas.x+canvas.width*.6,canvas.y+canvas.height*.35);await page.mouse.down();await page.mouse.move(canvas.x+canvas.width*.6+65,canvas.y+canvas.height*.35+30,{steps:12});await page.mouse.up();
 await page.waitForFunction(old=>JSON.stringify(JSON.parse(document.querySelector('#export').value).harbors.seattle.og.focus)!==JSON.stringify(old),before);
 const afterDrag=(await state()).harbors.seattle.og;
 const projection=await frame().evaluate(focus=>{const root=document.querySelector('.poc'),map=root.__portOfCallMap;const p=map.project(focus);return[p.x,p.y];},afterDrag.focus);assert.ok(projection.every(Number.isFinite));
 await page.locator('[data-device=x]').click();await ready();assert.equal(await page.locator('#zoom').inputValue(),'12');assert.ok(!(await state()).harbors.seattle.x);
 await page.locator('#minus').click();await page.waitForFunction(()=>JSON.parse(document.querySelector('#export').value).harbors.seattle.x?.zoom===11.75);
 assert.deepEqual((await state()).harbors.seattle.og,afterDrag);
 await page.locator('#orientation').selectOption('portrait');await ready();assert.equal(await page.locator('#zoom').inputValue(),'11.75');
 await page.locator('#harbor').selectOption('helsinki');await ready();assert.equal(await page.locator('.poi').count(),7);assert.equal(await page.locator('#fact option').count(),11);
 await page.locator('#fact').selectOption('helsinki:1');await page.waitForFunction(()=>document.querySelector('.poi.related')?.innerText.includes('Suomenlinna'));
 await page.locator('#harbor').selectOption('seattle');await ready();await page.locator('[data-device=og]').click();await ready();await page.locator('#orientation').selectOption('landscape');await ready();
 await page.locator('#fit').click();await page.waitForFunction(()=>Number.isInteger(Number(document.querySelector('#zoom').value)));
 const fit=await frame().evaluate(()=>document.querySelector('.poc').__portOfCallMap.getZoom());assert.ok(Number.isInteger(fit));
 const share=await page.evaluate(async()=>{const{draftHash}=await import('./draft.mjs');return location.href.split('#')[0]+'#draft='+draftHash(JSON.parse(document.querySelector('#export').value));});
 const exported=await state();await page.screenshot({path:'docs/screenshots/framing-editor.png'});
 await page.evaluate(()=>localStorage.clear());await page.goto(share);await page.reload();await ready();assert.deepEqual((await state()).harbors,exported.harbors);
 const checked=[];
 for(const harbor of catalog.harbors){await page.locator('#harbor').selectOption(harbor.id);await ready();assert.equal(await page.locator('.poi').count(),catalog.landmarks[harbor.id].length);checked.push(harbor.id);}
 assert.equal(await readFile('port_of_call/harbors.json','utf8'),registry,'Preview must not modify production framing');
 assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 const report={nativeOptions,requestedFractional:11.25,actualFractionalAfterReady:fractional,actualHalfZoomAfterReady:halfZoom,checkedHarbors:checked,nativeFitZoom:fit,ogXIndependent:true,pointerDrag:true,draftReload:true,shareLinkRoundTrip:true,harbors:16,pois:97,registryUnchanged:true,errors,failed};
 await writeFile('var/framing-editor-check.json',JSON.stringify(report,null,2)+'\n');console.log(report);
}finally{await browser.close();}
