// Runs in Chromium against the final pixels after the framework/font pass.
export function geometry(root=document.querySelector('.poc')) {
 const map=root.__portOfCallMap,m=root.getBoundingClientRect();
 const rect=n=>{const r=n.getBoundingClientRect();return [r.left-m.left,r.top-m.top,r.right-m.left,r.bottom-m.top];};
 const hit=(a,b)=>a[0]<b[2]-.5&&b[0]<a[2]-.5&&a[1]<b[3]-.5&&b[1]<a[3]-.5;
 const inside=b=>b[0]>=-1&&b[1]>=-1&&b[2]<=m.width+1&&b[3]<=m.height+1;
 const card=rect(root.querySelector('[data-poc-box]'));
 const attribution=root.querySelector('.map__attribution'),credit=attribution?rect(attribution):null;
 const nodes=[...root.querySelectorAll('.poc__ship')];
 const ships=nodes.map(n=>({id:n.dataset.id,box:rect(n.querySelector('svg'))}));
 let maxProjectionError=0;
 nodes.forEach(n=>{
  const r=rect(n),p=map.project([Number(n.dataset.lon),Number(n.dataset.lat)]);
  maxProjectionError=Math.max(maxProjectionError,Math.hypot((r[0]+r[2])/2-p.x,(r[1]+r[3])/2-p.y));
 });
 const labels=[...root.querySelectorAll('.poc__label')].map(rect);
 const reserved=[card,...(credit?[credit]:[])];
 let labelCollisions=0,leaderCollisions=0;
 labels.forEach((r,i)=>{if(ships.some(s=>hit(r,s.box))||reserved.some(b=>hit(r,b))||labels.slice(0,i).some(b=>hit(r,b)))labelCollisions++;});
 root.querySelectorAll('.poc__leader').forEach(l=>{
  const line=['x1','y1','x2','y2'].map(k=>Number(l.getAttribute(k)));
  const obstacles=labels.concat(reserved,ships.filter(s=>s.id!==l.dataset.id).map(s=>s.box));
  // The endpoint may touch its associated label's border. Slightly shorten for that check.
  const dx=line[2]-line[0],dy=line[3]-line[1],length=Math.hypot(dx,dy);
  const inset=length>0?Math.min(.5/length,.1):0;
  const shortened=[line[0]+dx*inset,line[1]+dy*inset,line[2]-dx*inset,line[3]-dy*inset];
  if(window.PortOfCallLabels.lineHits(shortened,obstacles))leaderCollisions++;
 });
 return {cardInside:inside(card),attributionClear:!!credit&&!hit(card,credit),
  hiddenShips:ships.filter(s=>reserved.some(b=>hit(s.box,b))).length,
  maxProjectionError,labelCollisions,leaderCollisions,
  labelsOutside:labels.filter(b=>!inside(b)).length,labels:labels.length,
  leaders:root.querySelectorAll('.poc__leader').length,
  textOverflow:[...root.querySelectorAll('[data-poc-box] > span')].filter(n=>n.offsetWidth&&n.scrollWidth>n.clientWidth+2).length};
}
