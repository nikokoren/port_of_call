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
 const fixed=[card,...(credit?[credit]:[])];
 const overlayNode=root.querySelector('[data-poc-spotlight]');
 const overlay=overlayNode&&Number(getComputedStyle(overlayNode).opacity)>0?rect(overlayNode):null;
 const reserved=fixed.concat(overlay?[overlay]:[]);
 let labelCollisions=0,leaderCollisions=0;
 labels.forEach((r,i)=>{if(ships.some(s=>hit(r,s.box))||reserved.some(b=>hit(r,b))||labels.slice(0,i).some(b=>hit(r,b)))labelCollisions++;});
 root.querySelectorAll('.poc__leader').forEach(l=>{
  const line=['x1','y1','x2','y2'].map(k=>Number(l.getAttribute(k)));
  const primary=!!l.closest('.poc__spotlight-lines');
  // The extended label may cover context ships; its connector may pass them.
  // Ordinary labels still avoid every ship and both information overlays.
  const obstacles=labels.concat(reserved,primary?[]:ships.filter(s=>s.id!==l.dataset.id).map(s=>s.box));
  // The endpoint may touch its associated label's border. Slightly shorten for that check.
  const dx=line[2]-line[0],dy=line[3]-line[1],length=Math.hypot(dx,dy);
  const inset=length>0?Math.min(.5/length,.1):0;
  const shortened=[line[0]+dx*inset,line[1]+dy*inset,line[2]-dx*inset,line[3]-dy*inset];
  if(window.PortOfCallLabels.lineHits(shortened,obstacles))leaderCollisions++;
 });
 const featured=ships.find(s=>s.id===root.dataset.focus);
 const connector=root.querySelector('.poc__spotlight-lines .poc__leader');
 let spotlightConnected=!root.dataset.focus;
 if(overlay&&connector){
  const x=+connector.getAttribute('x2'),y=+connector.getAttribute('y2');
  spotlightConnected=connector.dataset.id===root.dataset.focus&&
   x>=overlay[0]-.5&&x<=overlay[2]+.5&&y>=overlay[1]-.5&&y<=overlay[3]+.5&&
   Math.min(Math.abs(x-overlay[0]),Math.abs(x-overlay[2]),Math.abs(y-overlay[1]),Math.abs(y-overlay[3]))<.5;
 }
 return {cardInside:inside(card),attributionInside:!!credit&&inside(credit),attributionClear:!!credit&&!hit(card,credit),
  spotlightInside:!overlay||inside(overlay),spotlightClear:!overlay||(!fixed.some(b=>hit(overlay,b))&&(!featured||!hit(overlay,featured.box))),
  spotlightConnected,spotlightVisible:!!overlay,
  spotlightInverted:!root.dataset.focus||!!(overlay&&overlayNode.classList.contains('inverse')&&getComputedStyle(overlayNode).backgroundColor!==getComputedStyle(overlayNode.querySelector('.title')).color),
  spotlightStatsAligned:!overlay||(()=>{const vals=[...overlayNode.querySelectorAll('[data-poc-stat-value]')];return vals.length<2||Math.abs(vals[0].getBoundingClientRect().top-vals[1].getBoundingClientRect().top)<=1;})(),
  spotlightConnectorWidth:connector?parseFloat(getComputedStyle(connector).strokeWidth):0,
  spotlightSurface:overlay?getComputedStyle(overlayNode).backgroundColor:null,
  spotlightTextColor:overlay?getComputedStyle(overlayNode.querySelector('.title')).color:null,
  spotlightTextVisible:!root.dataset.focus||!!(overlay&&overlayNode.innerText.trim().length>12&&overlayNode.querySelector('.title')?.innerText.trim().length>=3&&[...overlayNode.children].filter(n=>n.textContent.trim()&&n.getBoundingClientRect().height>0).length>=3),occludedBySpotlight:overlay?ships.filter(s=>hit(s.box,overlay)).length:0,
  hiddenShips:ships.filter(s=>fixed.some(b=>hit(s.box,b))).length,
  maxProjectionError,labelCollisions,leaderCollisions,
  labelsOutside:labels.filter(b=>!inside(b)).length,labels:labels.length,
  leaders:root.querySelectorAll('.poc__leader').length,
  textOverflow:[...root.querySelectorAll('[data-poc-box] > span,[data-poc-spotlight] > span,[data-poc-stat-caption],[data-poc-stat-value]')].filter(n=>n.offsetWidth&&n.scrollWidth>n.clientWidth+2).length};
}
