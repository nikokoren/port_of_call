import {zoomValue} from './draft.mjs';
const session=document.querySelector('meta[name=framing-session]').content;
const send=(kind,rest={})=>parent.postMessage({kind,session,...rest},parent.location.origin);
let root,map,points=[],settings,suppress=false,userMove=false,disposed=false,scheduled=false;
const style=document.createElement('style');style.textContent='.frame-poi-pin{position:absolute;z-index:4;pointer-events:none}.frame-poi-label{position:absolute;z-index:4;pointer-events:none;white-space:nowrap}.frame-poi-line{position:absolute;inset:0;z-index:3;width:100%;height:100%;pointer-events:none}';document.head.append(style);
function scale(){return Math.max(1,parseFloat(getComputedStyle(root.closest('.screen')).getPropertyValue('--ui-scale'))||1);}
function rect(node){const a=root.getBoundingClientRect(),b=node.getBoundingClientRect(),k=a.width/root.offsetWidth;return[(b.left-a.left)/k,(b.top-a.top)/k,(b.right-a.left)/k,(b.bottom-a.top)/k];}
function padding(){const g=12*scale(),r=rect(root.querySelector('[data-poc-box]')),W=root.clientWidth,H=root.clientHeight;let p=(W-r[2])*H>=W*r[1]?{top:g,right:g,bottom:g,left:r[2]+g}:{top:g,right:g,bottom:H-r[1]+g,left:g};if(W-p.left-p.right<40||H-p.top-p.bottom<40)p={top:g,right:g,bottom:g,left:g};return p;}
function focus(){const p=padding();return map.unproject([root.clientWidth/2+(p.left-p.right)/2,root.clientHeight/2+(p.top-p.bottom)/2]).toArray().map(v=>Math.round(v*1e6)/1e6);}
function capture(){const camera={focus:focus(),zoom:zoomValue(map.getZoom()-Math.log2(scale()),settings.fractional)};root.dataset.center=camera.focus.join(',');root.dataset.zoom=camera.zoom;send('framing-change',{camera});}
function paint(){
 if(!settings||disposed)return;
 root.querySelectorAll('.frame-poi-pin,.frame-poi-label,.frame-poi-line').forEach(n=>n.remove());
 const W=root.clientWidth,H=root.clientHeight,unit=scale(),card=rect(root.querySelector('[data-poc-box]'));
 const credits=[...root.querySelectorAll('.map__attribution')].map(rect),boxes=[card,...credits],lines=[],statuses=[];
 const match=p=>p.fact_ids.includes(settings.fact?.fact_id),ordered=[...points].sort((a,b)=>Number(b.name===settings.selected)-Number(a.name===settings.selected)||Number(match(b))-Number(match(a)));
 const icons=ordered.map(point=>{const p=map.project(point.position);return[p.x-6*unit,p.y-16*unit,p.x+6*unit,p.y+unit];});
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('class','frame-poi-line');svg.setAttribute('viewBox',`0 0 ${W} ${H}`);root.append(svg);
 if(settings.coverage){const [w,s,e,n]=settings.bbox,a=map.project([w,n]),b=map.project([e,s]);const r=document.createElementNS('http://www.w3.org/2000/svg','rect');r.setAttribute('x',a.x);r.setAttribute('y',a.y);r.setAttribute('width',b.x-a.x);r.setAttribute('height',b.y-a.y);r.setAttribute('fill','none');r.setAttribute('stroke','#555');r.setAttribute('stroke-width',unit);r.setAttribute('stroke-dasharray','5 4');svg.append(r);}
 ordered.forEach((point,index)=>{
  const p=map.project(point.position),ib=icons[index],inside=p.x>=0&&p.y>=0&&p.x<W&&p.y<H,blocked=inside&&[card,...credits].some(b=>PortOfCallLabels.overlaps(ib,b));
  let state=!inside?'Outside view':blocked?'Under port card / credits':'On map';
  if(inside){
   const pin=document.createElementNS('http://www.w3.org/2000/svg','svg');pin.setAttribute('class','frame-poi-pin');pin.setAttribute('viewBox','0 0 12 18');pin.style.cssText=`left:${p.x-6*unit}px;top:${p.y-17*unit}px;width:${12*unit}px;height:${18*unit}px`;pin.dataset.name=point.name;
   pin.innerHTML='<path d="M6 17C4 13 1 10 1 6a5 5 0 1 1 10 0c0 4-3 7-5 11Z" fill="white" stroke="black" stroke-width="1.2"/><circle cx="6" cy="6" r="1.7" fill="black"/>';root.append(pin);
   if(settings.labels&&!blocked){
    const label=document.createElement('span');label.className='frame-poi-label bg--canvas label label--small'+(match(point)||point.name===settings.selected?' font--bold':'');label.textContent=point.name;root.append(label);
    const plan=PortOfCallLabels.plan({x:p.x,y:p.y-8*unit,icon:ib,width:label.offsetWidth+4,height:label.offsetHeight+2,W,H,boxes:boxes.concat(icons),lines,scale:unit});
    if(plan){label.style.left=plan.rect[0]+2+'px';label.style.top=plan.rect[1]+1+'px';boxes.push(plan.rect);if(plan.line){lines.push(plan.line);const l=document.createElementNS('http://www.w3.org/2000/svg','line');['x1','y1','x2','y2'].forEach((key,i)=>l.setAttribute(key,plan.line[i]));l.setAttribute('stroke','black');l.setAttribute('stroke-width',unit);svg.append(l);}}
    else{label.remove();state='Pin visible · label crowded';}
   }
  }
  statuses.push({name:point.name,state});
 });
 send('framing-pois',{points:statuses});
}
function queuePaint(){if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;paint();});}
window.framingEditor={
 setPoints(value){points=value;},
 apply(value){
  settings=value;const c=value.camera;root.dataset.center=c.focus.join(',');root.dataset.zoom=c.zoom;
  const fact=root.querySelector('[data-poc-port-fact]');if(fact){fact.hidden=!value.facts;fact.textContent=value.fact?.text||'';}
  window.terminalize?.();const p=padding();suppress=true;map.jumpTo({center:c.focus,zoom:c.zoom+Math.log2(scale())});map.easeTo({center:c.focus,offset:[(p.left-p.right)/2,(p.top-p.bottom)/2],duration:0});suppress=false;queuePaint();
 },
 fitPoints(){if(!settings||!points.length)return;suppress=true;TRMNLMaps.fit(map,points.map(p=>p.position),{padding:padding(),maxZoom:16});suppress=false;capture();queuePaint();},
 dispose(){disposed=true;map?.remove();}
};
async function start(){
 for(let i=0;i<600&&!disposed;i++){
  root=document.querySelector('.poc');
  if(root?.dataset.mapReady==='error'){send('framing-error',{message:'The native map could not load. Check your connection and reload.'});return;}
  if(root?.dataset.mapReady==='true'&&window.TRMNL_PLUGINS_READY===true)break;
  await new Promise(r=>setTimeout(r,100));
 }
 if(disposed)return;map=root?.__portOfCallMap;if(!map){send('framing-error',{message:'Map loading timed out. Reload to try again.'});return;}
 map.dragPan.enable();map.scrollZoom.enable();map.doubleClickZoom.disable();map.touchZoomRotate.enable();map.touchZoomRotate.disableRotation();
 map.on('dragstart',()=>{userMove=true;});map.on('zoomstart',event=>{if(event.originalEvent)userMove=true;});
 map.on('moveend',()=>{if(!suppress&&userMove&&settings){userMove=false;const zoom=zoomValue(map.getZoom()-Math.log2(scale()),settings.fractional);suppress=true;map.jumpTo({zoom:zoom+Math.log2(scale())});suppress=false;capture();}queuePaint();});
 map.on('move',queuePaint);new ResizeObserver(queuePaint).observe(root.querySelector('[data-poc-box]'));
 send('framing-ready');
}
start().catch(e=>send('framing-error',{message:e.message}));
