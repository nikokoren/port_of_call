import {DRAFT_KIND,cameraFor,zoomValue,validateDraft,setCamera,draftHash,readDraftHash} from './draft.mjs';
const $=id=>document.getElementById(id),key='poc-harbor-framing-v1';
const data=await fetch('data.json').then(r=>{if(!r.ok)throw new Error('Framing data unavailable');return r.json();});
const ports=data.harbors,byId=new Map(ports.map(p=>[p.id,p]));
let draft={kind:DRAFT_KIND,schema_version:1,base_revision:data.revision,harbors:{}},device='og',ready=false,selected=null,generation=0,startupNotice='';
try{const saved=localStorage.getItem(key);if(saved)draft=validateDraft(JSON.parse(saved),ports);}catch{startupNotice='A saved draft could not be read. Start a new draft or reopen its share link.';}
try{if(location.hash.startsWith('#draft=')){const shared=readDraftHash(location.hash,ports);for(const [id,profiles] of Object.entries(shared.harbors))draft.harbors[id]={...draft.harbors[id],...profiles};}}catch(e){startupNotice=e.message;}
for(const p of ports)$('harbor').add(new Option(p.name.split(' — ')[0]+', '+p.country,p.id));
$('harbor').value=byId.has('seattle')?'seattle':ports[0].id;
const port=()=>byId.get($('harbor').value),current=()=>cameraFor(port(),draft,device),bridge=()=>$('preview').contentWindow?.framingEditor;
function exportDraft(){return JSON.stringify(draft,null,2);}
function save(){
 const count=Object.values(draft.harbors).reduce((n,p)=>n+Object.keys(p).length,0);
 try{localStorage.setItem(key,JSON.stringify(draft));$('saved').textContent=count?`${count} device view${count===1?'':'s'} saved as a draft · recipe unchanged`:'No framing changes yet';}catch{$('saved').textContent='Draft is kept in this tab; browser storage is unavailable.';}
 $('export').value=exportDraft();$('copy').disabled=$('share').disabled=!count;
}
function readout(){const c=current();$('zoom').value=c.zoom;$('longitude').value=c.focus[0].toFixed(6);$('latitude').value=c.focus[1].toFixed(6);$('fractional').checked=$('fractional').checked||!Number.isInteger(c.zoom);help();save();}
function help(){const fractional=$('fractional').checked;$('zoom-help').textContent=fractional?'Experimental: fractional zoom bypasses native camera/dither-origin alignment.':'Whole-number zoom keeps the native framework’s pixel alignment.';$('zoom-help').classList.toggle('experimental',fractional);}
function fact(){return data.facts[port().id].find(f=>f.fact_id===$('fact').value);}
function options(){return{camera:current(),fractional:$('fractional').checked,facts:$('facts').checked,fact:fact(),labels:$('labels').checked,coverage:$('coverage').checked,bbox:port().bbox,selected};}
function update(){if(ready)bridge()?.apply(options());}
function edit(c){try{setCamera(draft,port(),device,c);readout();update();}catch(e){$('message').textContent=e.message;}}
function resize(){const big=device==='x',portrait=$('orientation').value==='portrait';const [w,h]=big?(portrait?[1404,1872]:[1872,1404]):portrait?[480,800]:[800,480];const factor=$('display').value==='actual'?1:Math.min(1,($('canvas').clientWidth-32)/w,($('canvas').clientHeight-32)/h);const frame=$('preview');frame.style.width=w+'px';frame.style.height=h+'px';frame.style.transform=`scale(${factor})`;$('frame-holder').style.width=w*factor+'px';$('frame-holder').style.height=h*factor+'px';}
function poiList(states=[]){
 const matched=new Set(data.landmarks[port().id].filter(p=>p.fact_ids.includes($('fact').value)).map(p=>p.name));
 $('pois').replaceChildren();$('poi-heading').textContent=`Selected POIs · ${data.landmarks[port().id].length}`;
 for(const point of data.landmarks[port().id]){
  const row=document.createElement('div');row.className='poi'+(matched.has(point.name)?' related':'');
  const pick=document.createElement('button');pick.textContent=point.name;pick.title=point.source_url;const status=document.createElement('span');status.textContent=states.find(s=>s.name===point.name)?.state||'Loading location…';pick.append(status);
  pick.onclick=()=>{selected=point.name;update();};const center=document.createElement('button');center.textContent='Center';center.setAttribute('aria-label','Center on '+point.name);center.onclick=()=>edit({focus:point.position,zoom:current().zoom});row.append(pick,center);$('pois').append(row);
 }
}
function load(){
 ready=false;selected=null;generation++;bridge()?.dispose();
 const p=port(),big=device==='x',portrait=$('orientation').value==='portrait',w=portrait?(big?780:480):(big?1040:800),h=portrait?(big?1040:800):(big?780:480);
 $('fact').replaceChildren();for(const f of data.facts[p.id])$('fact').add(new Option(f.text,f.fact_id));
 $('fact-copy').textContent=fact().text;$('preview-title').textContent=`${p.name.split(' — ')[0]} · ${big?'TRMNL X':'TRMNL OG'} · ${portrait?'Portrait':'Landscape'}`;
 $('other').textContent='Copy framing to '+(big?'OG':'X');$('message').textContent='Loading the native map…';
 readout();poiList();resize();
 const base=new URL('./',location.href).href;
 $('preview').srcdoc=`<!doctype html><html><head><meta charset="utf-8"><meta name="framing-session" content="${generation}"><base href="${base}"><link rel="stylesheet" href="assets/plugins.css"><script src="assets/plugins.js"></script><style>html,body{margin:0;padding:0;background:white}.screen{isolation:isolate;position:relative!important;width:${w}px!important;height:${h}px!important;--screen-w:${w}px;--screen-h:${h}px;--device-ui-scale:1;--ui-scale:1;--content-scale:1;--color-depth:${big?4:1}}.preview-view{position:absolute;inset:0;width:100%;height:100%}</style></head><body class="trmnl"><div class="screen screen--no-bleed screen--${big?'v2':'og'} screen--${big?'lg':'md'} screen--${big?'4':'1'}bit ${portrait?'screen--portrait':''}"><div class="preview-view view view--full">${data.markup[p.id]}</div></div><script type="module" src="bridge.mjs"></script></body></html>`;
}
window.addEventListener('message',event=>{
 if(event.source!==$('preview').contentWindow||event.origin!==location.origin)return;
 const m=event.data;if(!m||typeof m!=='object'||m.session!==String(generation))return;
 if(m.kind==='framing-ready'){ready=true;bridge().setPoints(data.landmarks[port().id]);update();$('message').textContent=startupNotice||'Drag to pan. Use + / − or the zoom field to change the framing.';startupNotice='';}
 if(m.kind==='framing-change'){try{setCamera(draft,port(),device,m.camera);readout();}catch(e){$('message').textContent=e.message;}}
 if(m.kind==='framing-pois')poiList(m.points);
 if(m.kind==='framing-error')$('message').textContent=m.message;
});
$('harbor').onchange=load;$('orientation').onchange=load;
for(const b of document.querySelectorAll('[data-device]'))b.onclick=()=>{device=b.dataset.device;for(const peer of document.querySelectorAll('[data-device]'))peer.setAttribute('aria-pressed',String(peer===b));load();};
$('zoom').onchange=()=>{try{edit({...current(),zoom:zoomValue($('zoom').value,$('fractional').checked)});}catch(e){$('message').textContent=e.message;}};
$('fractional').onchange=()=>{help();if(!$('fractional').checked)edit({...current(),zoom:zoomValue(current().zoom)});else update();};
for(const [id,sign] of [['minus',-1],['plus',1]])$(id).onclick=()=>edit({...current(),zoom:zoomValue(current().zoom+sign*($('fractional').checked?.25:1),$('fractional').checked)});
$('apply').onclick=()=>{if(!$('longitude').value.trim()||!$('latitude').value.trim()){$('message').textContent='Enter both latitude and longitude.';return;}edit({focus:[Number($('longitude').value.replace(',','.')),Number($('latitude').value.replace(',','.'))],zoom:current().zoom});};
$('fit').onclick=()=>bridge()?.fitPoints();$('reset').onclick=()=>edit(cameraFor(port(),{harbors:{}},device));
$('other').onclick=()=>{setCamera(draft,port(),device==='og'?'x':'og',current());save();$('message').textContent='Copied to the other device draft.';};
$('fact').onchange=()=>{$('fact-copy').textContent=fact().text;update();};for(const id of ['facts','labels','coverage'])$(id).onchange=update;
$('display').onchange=resize;new ResizeObserver(resize).observe($('canvas'));
async function copy(value,label){try{await navigator.clipboard.writeText(value);$('message').textContent=label;}catch{$('export').value=value;$('export').closest('details').open=true;$('export').select();$('message').textContent='Select and copy the draft below.';}}
$('copy').onclick=()=>copy(exportDraft(),'Changes copied. Paste them into the chat when ready.');$('share').onclick=()=>copy(location.href.split('#')[0]+'#draft='+draftHash(draft),'Draft link copied. Paste it into the chat when ready.');
load();
