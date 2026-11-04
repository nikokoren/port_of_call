// Map-only review of candidate bounds. No vessel records or simulated traffic.
import http from 'node:http';
import path from 'node:path';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {chromium} from 'playwright';
import {render} from './render.mjs';
import {previewPixels} from './preview-pixels.mjs';
const harbors=JSON.parse(await readFile('port_of_call/harbors.json','utf8')).filter(h=>h.collection==='major15');
const pages=new Map();
for(const h of harbors){
 const data={port:h,viewport:h.bbox,status:'unavailable',message:'Map extent review · no vessel data included',
             source:'Map-only preview · not current traffic',total:0,vessels:[]};
 let markup=(await render('full',data)).replaceAll('https://trmnl.com/js/maplibre-gl/5.24.0/','/assets/');
 markup=markup.replace('data-poc-total>0','data-poc-total>—').replace('vessel reports','no AIS data in preview')
   .replace('No recent observation','Harbor extent preview').replace('Fetched —','Map framing preview only');
 pages.set('/'+h.id,`<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="/assets/plugins.css"><script src="/assets/plugins.js"></script>
 <style>html,body{margin:0;padding:0}.screen{width:800px!important;height:480px!important;isolation:isolate}.view{position:absolute;inset:0;width:100%;height:100%}</style></head>
 <body class="trmnl"><div class="screen screen--og screen--md screen--2bit"><div class="view view--full">${markup}</div></div></body></html>`);
}
const server=http.createServer(async(req,res)=>{
 try {
  if(pages.has(req.url)){res.setHeader('Content-Type','text/html');res.end(pages.get(req.url));return;}
  let file;
  if(req.url.startsWith('/assets/'))file=path.resolve('var/assets',req.url.slice(8));
  else if(req.url.startsWith('/fonts/'))file=path.resolve('var/assets',req.url.slice(1));
  if(!file||!file.startsWith(path.resolve('var/assets')+path.sep)){res.statusCode=404;res.end();return;}
  res.setHeader('Content-Type',file.endsWith('.css')?'text/css':file.endsWith('.js')?'text/javascript':'application/octet-stream');
  res.end(await readFile(file));
 }catch{res.statusCode=500;res.end('Preview asset unavailable');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
await mkdir('var/major-frames',{recursive:true});
const results=[];
try {
 for(const h of harbors){
  const page=await browser.newPage({viewport:{width:800,height:480}});
  if(process.env.MAP_RELAY==='true')await page.route(/^https:\/\/(maps\.trmnl\.com|trmnl\.com|usetrmnl\.com)\//,async route=>{
   const r=await fetch('http://127.0.0.1:8788/?url='+encodeURIComponent(route.request().url()));
   await route.fulfill({status:r.status,body:Buffer.from(await r.arrayBuffer()),contentType:r.headers.get('content-type')||'application/octet-stream'});
  });
  await page.goto(origin+'/'+h.id);
  await page.waitForFunction(()=>document.querySelector('.poc')?.dataset.mapReady==='true',{timeout:35000});
  await page.waitForFunction(()=>window.TRMNL_PLUGINS_READY===true,{timeout:25000});
  const pixels=previewPixels(await page.locator('.screen').screenshot({path:'var/major-frames/'+h.id+'.png'}));
  results.push({id:h.id,kind:'map-only extent review',aisDataIncluded:false,pixels});
  console.log(h.id,'map frame rendered; no AIS data');await page.close();
 }
 await writeFile('var/major-frames/results.json',JSON.stringify(results,null,2)+'\n');
}finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
