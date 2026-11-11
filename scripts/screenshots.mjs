import {chromium} from 'playwright';
import {geometry} from './visual-geometry.mjs';
import {previewPixels} from './preview-pixels.mjs';
import {mkdir,writeFile} from 'node:fs/promises';
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const cases=[
 ['og-helsinki','full','og','helsinki'],['og-turku','full','og','turku'],['og-rauma','full','og','rauma'],
 ['og-half-horizontal','half_horizontal','og','helsinki'],['og-half-vertical','half_vertical','og','helsinki'],
 ['og-quadrant','quadrant','og','helsinki'],['x-landscape','full','x','helsinki'],['x-portrait','full','portrait','turku'],
 ['x-half-horizontal','half_horizontal','x','helsinki'],['x-half-vertical','half_vertical','x','turku'],['x-quadrant','quadrant','x','rauma'],
 ['og-dark','full','og','helsinki',true],['og-one-bit','full','onebit','helsinki'],['og-empty','quadrant','og','empty'],
 ['og-stale','full','og','stale'],['og-unavailable','half_horizontal','og','unavailable'],['og-warming','quadrant','og','warming'],
 ['og-map-error','full','og','helsinki',false,true],
 ['og-demo-density','full','og','demo'],
 ['spotlight-full','full','og','rauma-spotlight'],['spotlight-half-horizontal','half_horizontal','og','helsinki-spotlight'],
 ['spotlight-half-vertical','half_vertical','og','turku-spotlight'],['spotlight-quadrant','quadrant','og','rauma-spotlight'],
 ['spotlight-x','full','x','turku-spotlight'],['spotlight-portrait','full','portrait','helsinki-spotlight'],
 ['spotlight-layout-test','quadrant','og','spotlight-layout-test'],['spotlight-fallback','quadrant','og','spotlight-fallback'],
 ['spotlight-one-bit','full','onebit','helsinki-spotlight'],['spotlight-dark','full','og','turku-spotlight',true],
 ['spotlight-one-bit-dark','full','onebit','helsinki-spotlight',true],
 ['labels-overview','full','og','rauma-labels',false,false,'on'],
 ['labels-overview-dark','full','og','rauma-labels',true,false,'on'],
 ['labels-spotlight','full','og','rauma-spotlight',false,false,'on'],
 ['labels-spotlight-dark','full','og','rauma-spotlight',true,false,'on'],
 ['labels-spotlight-half-horizontal','half_horizontal','og','helsinki-spotlight',false,false,'on'],
 ['labels-spotlight-quadrant','quadrant','og','rauma-spotlight',false,false,'on'],
 ['facts-full','full','og','rauma-labels',false,false,'on',true],
 ['facts-full-dark','full','og','rauma-spotlight',true,false,'on',true],
 ['facts-half-vertical','half_vertical','og','turku-spotlight',false,false,'on',true],
 ['facts-quadrant','quadrant','og','rauma-spotlight',false,false,'on',true],
 ['facts-x-quadrant','quadrant','x','rauma-spotlight',false,false,'on',true],
 ['facts-portrait','full','portrait','helsinki-spotlight',false,false,'on',true],
 ['legend-overview','full','og','rauma-labels',false,false,'on',true,true],
 ['legend-spotlight','full','og','rauma-spotlight',false,false,'on',true,true],
 ['legend-dark','full','og','rauma-spotlight',true,false,'on',true,true],
 ['legend-one-bit','full','onebit','rauma-labels',false,false,'on',true,true],
 ['legend-x','full','x','turku-spotlight',false,false,'on',true,true],
 ['legend-portrait','full','portrait','helsinki-spotlight',false,false,'on',true,true],
 ['legend-og-portrait','full','og-portrait','rauma-spotlight',false,false,'on',true,true],
 ['legend-seattle','full','onebit','seattle-legend',false,false,'on',true,true],
 ['legend-seattle-x','full','x','seattle-legend',false,false,'on',true,true]
];
await mkdir('docs/screenshots',{recursive:true});
const results=[];
try {
 for(const [name,layout,device,fixture,dark=false,blockTiles=false,labels=fixture.endsWith('-spotlight')?'off':'on',facts=false,legend=false] of cases.filter(c=>!process.env.CASE_PREFIX||c[0].startsWith(process.env.CASE_PREFIX))){
  // X: 1040x780 CSS at 1.8x, i.e. the real 1872x1404 panel.
  const page=await browser.newPage({viewport:{width:device==='portrait'?780:device==='og-portrait'?480:device==='x'?1040:800,height:device==='portrait'?1040:device==='og-portrait'?800:device==='x'?780:480},deviceScaleFactor:device==='x'||device==='portrait'?1.8:1});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  if(blockTiles)await page.route(/^https:\/\/maps\.trmnl\.com\//,r=>r.abort());
  if(process.env.MAP_RELAY==='true')await page.route(/^https:\/\/(maps\.trmnl\.com|trmnl\.com|usetrmnl\.com)\//,async route=>{
   if(blockTiles&&route.request().url().startsWith('https://maps.trmnl.com/')){await route.abort();return;}
   try{const r=await fetch('http://127.0.0.1:8788/?url='+encodeURIComponent(route.request().url()));
    await route.fulfill({status:r.status,body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'application/octet-stream'});
   }catch{await route.abort();}
  });
  await page.goto(`http://127.0.0.1:8787/?layout=${layout}&device=${device}&fixture=${fixture}&labels=${labels}&dark=${dark}&facts=${facts}&legend=${legend}`);
  await page.waitForFunction(()=>document.querySelector('.poc')?.dataset.mapReady,{timeout:35000});
  await page.evaluate(()=>document.fonts.ready);
  await page.waitForFunction(()=>window.TRMNL_PLUGINS_READY===true,{timeout:25000});
  const status=await page.evaluate(()=>({ready:document.querySelector('.poc').dataset.mapReady,
   markers:document.querySelectorAll('.poc__ship').length,attribution:document.body.innerText.includes('OpenStreetMap'),
   overflow:document.querySelector('.poc').scrollHeight>document.querySelector('.poc').clientHeight+Math.max(1,parseFloat(getComputedStyle(document.querySelector('.screen')).getPropertyValue('--ui-scale'))||1),
   text:document.querySelector('.poc__notice').innerText}));
  const positions=await page.evaluate(geometry);
  if(positions.legendVisible!==legend||!positions.legendInside||!positions.legendClear||!positions.legendIconsValid||!positions.legendDocked||!positions.legendCompact)throw new Error(name+': legend '+JSON.stringify(positions));
  if(facts&&positions.portFactVisible!==(layout!=='quadrant'||device==='x'))throw new Error(name+': unexpected port-fact visibility');
  if(name.startsWith('labels-')&&layout==='full'&&(positions.labels<1||positions.labelRoutes<1))throw new Error(name+': voyage labels absent');
  if(name==='spotlight-half-horizontal'&&status.markers<2)throw new Error(name+': camera lost all context vessels');
  if(fixture.endsWith('-spotlight')||fixture==='spotlight-layout-test'){
   const subject=await page.evaluate(()=>{const el=document.querySelector('.poc'),id=el.dataset.focus;return {marker:!!el.querySelector('.poc__ship--featured[data-id="'+id+'"]'),label:!!el.querySelector('[data-poc-spotlight][data-id="'+id+'"]')};});
   if(positions.spotlightConnectorWidth<3)throw new Error(name+': Spotlight connector too thin');
   if(!subject.marker||!subject.label)throw new Error(name+': featured subject missing '+JSON.stringify(subject));
  }
  if(!blockTiles && (!positions.labelContentsValid||!positions.spotlightTextConsistent||!positions.spotlightInverted||!positions.spotlightTextVisible||!positions.spotlightInside||!positions.spotlightClear||!positions.spotlightConnected||!positions.cardInside||!positions.cardAtCorner||!positions.attributionInside||!positions.attributionClear||!positions.attributionTight||positions.hiddenShips||positions.maxProjectionError>1||positions.labelCollisions||positions.leaderCollisions||positions.labelsOutside||positions.textOverflow))throw new Error(name+': geometry '+JSON.stringify(positions));
  if(errors.length||status.ready!==(blockTiles?'error':'true')||!status.attribution||status.overflow)throw new Error(name+': '+JSON.stringify({status,errors}));
  if(!blockTiles && ['helsinki','turku','rauma','demo','stale'].includes(fixture)&&status.markers===0)throw new Error(name+': no markers');
  if(!blockTiles && status.markers) {
   const aboveDither=await page.evaluate(()=>[...document.querySelectorAll('.poc__ship')].every(m=>Number(getComputedStyle(m).zIndex)>0));
   if(!aboveDither)throw new Error(name+': glyphs may be covered by native dither canvas');
  }
  const pixels=previewPixels(await page.locator('.screen').screenshot({path:`docs/screenshots/${name}.png`}));
  results.push({name,...status,geometry:positions,pixels,errors});console.log(name,status.markers,'markers',positions.labels,'labels',positions.leaders,'leaders');await page.close();
 }
 await writeFile(process.env.CASE_PREFIX?'var/visual-subset.json':'docs/screenshots/results.json',JSON.stringify(results,null,2)+'\n');
}finally{await browser.close();}
