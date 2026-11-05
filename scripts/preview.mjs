import http from 'node:http';
import path from 'node:path';
import {readFile} from 'node:fs/promises';
import {render,layouts} from './render.mjs';
const types={'.css':'text/css','.js':'text/javascript','.ttf':'font/ttf','.woff2':'font/woff2','.png':'image/png'};
http.createServer(async(req,res)=>{
 try {
  const u=new URL(req.url,'http://localhost');
  if(u.pathname.startsWith('/assets/')||u.pathname.startsWith('/fonts/')) {
   const rel=u.pathname.startsWith('/fonts/')?u.pathname.slice(1):u.pathname.slice(8);
   const file=path.resolve('var/assets',rel);
   if(!file.startsWith(path.resolve('var/assets')+path.sep))throw new Error('path');
   res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(await readFile(file));return;
  }
  const layout=u.searchParams.get('layout')||'full';
  if(!layouts.includes(layout))throw new Error('layout');
  const fixture=u.searchParams.get('fixture')||'helsinki';
  if(!/^[a-z_-]+$/.test(fixture))throw new Error('fixture');
  const data=JSON.parse(await readFile('fixtures/'+fixture+'.json','utf8'));
  let markup=(await render(layout,data,{ship_labels:u.searchParams.get('labels')||'off'}))
   .replaceAll('https://trmnl.com/js/maplibre-gl/5.24.0/','/assets/');
  let provenance='';
  if(!data.demo) {
    const date=new Date(data.snapshot_at).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'});
    const tag=(['stale','empty','unavailable','warming'].includes(fixture)||fixture.startsWith('spotlight-layout-test')||fixture==='spotlight-fallback')?'STATE TEST · archive':'Archive';
    provenance=`<div class="description p--2" data-preview-provenance>${tag} · ${date} · Historical test capture, not current traffic</div>`;
  }
  const device=u.searchParams.get('device')||'og';
  const x=device==='x'||device==='portrait';
  const [w,h]=device==='portrait'?[1404,1872]:x?[1872,1404]:[800,480];
  const dark=u.searchParams.get('dark')==='true';
  // Dimensions use the requested X panel; no assumption about evolving device aliases.
  const mashup=u.searchParams.get('mashup')==='true'&&layout!=='full';
  const width=!mashup&&(layout==='half_vertical'||layout==='quadrant')?w/2:w;
  const height=!mashup&&(layout==='half_horizontal'||layout==='quadrant')?h/2:h;
  const one=`<div class="${mashup?'':'preview-view '}view view--${layout}">${markup}</div>`;
  const kind={half_horizontal:'1Tx1B',half_vertical:'1Lx1R',quadrant:'2x2'}[layout];
  const inner=mashup?`<div class="mashup mashup--${kind}">${one.repeat(layout==='quadrant'?4:2)}</div>`:one;
  res.setHeader('Content-Type','text/html');res.end(`<!DOCTYPE html><html><head><meta charset="utf-8">
   <link rel="stylesheet" href="/assets/plugins.css"><script src="/assets/plugins.js"></script>
   <style>html,body{margin:0;padding:0;background:white}.screen{isolation:isolate;position:relative!important;width:${width}px!important;height:${height}px!important;--screen-w:${w}px;--screen-h:${h}px;--device-ui-scale:${x?2:1};--ui-scale:${x?2:1};--content-scale:1;--color-depth:${x?4:device==='onebit'?1:2}}
   .preview-view{position:absolute;inset:0;width:100%;height:100%}</style></head>
   <body class="trmnl">${provenance}<div class="screen screen--${x?'lg':'og'} screen--${x?'lg':'md'} screen--${x?'4':device==='onebit'?'1':'2'}bit ${dark?'screen--dark-mode':''} ${device==='portrait'?'screen--portrait':''}">${inner}</div></body></html>`);
 } catch(e) {res.statusCode=500;res.end(e.message);}
}).listen(8787,'127.0.0.1',()=>console.log('Preview renderer listening on port 8787'));
