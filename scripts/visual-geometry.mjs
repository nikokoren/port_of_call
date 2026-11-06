// Runs in Chromium against the final pixels after the framework/font pass.
export function geometry(root=document.querySelector('.poc')) {
 const map=root.__portOfCallMap,m=root.getBoundingClientRect();
 // A layout that cannot show the subject without moving the harbor view draws the overview instead.
 const focusId=root.dataset.spotlightFallback==='true'?'':root.dataset.focus;
 const rect=n=>{const r=n.getBoundingClientRect();return [r.left-m.left,r.top-m.top,r.right-m.left,r.bottom-m.top];};
 const hit=(a,b)=>a[0]<b[2]-.5&&b[0]<a[2]-.5&&a[1]<b[3]-.5&&b[1]<a[3]-.5;
 const inside=b=>b[0]>=-1&&b[1]>=-1&&b[2]<=m.width+1&&b[3]<=m.height+1;
 const card=rect(root.querySelector('[data-poc-box]'));
 const credits=[...root.querySelectorAll('.map__attribution')].flatMap(n=>[...n.getClientRects()].map(r=>[r.left-m.left,r.top-m.top,r.right-m.left,r.bottom-m.top]));
 const nodes=[...root.querySelectorAll('.poc__ship')];
 const ships=nodes.map(n=>({id:n.dataset.id,box:rect(n.querySelector('svg'))}));
 let maxProjectionError=0;
 nodes.forEach(n=>{
  const r=rect(n),p=map.project([Number(n.dataset.lon),Number(n.dataset.lat)]);
  maxProjectionError=Math.max(maxProjectionError,Math.hypot((r[0]+r[2])/2-p.x,(r[1]+r[3])/2-p.y));
 });
 const labels=[...root.querySelectorAll('.poc__label')].map(rect);
 const fixed=[card,...credits];
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
 const featured=ships.find(s=>s.id===focusId);
 const connector=root.querySelector('.poc__spotlight-lines .poc__leader');
 let spotlightConnected=!focusId;
 if(overlay&&connector){
  const x=+connector.getAttribute('x2'),y=+connector.getAttribute('y2');
  spotlightConnected=connector.dataset.id===focusId&&
   x>=overlay[0]-.5&&x<=overlay[2]+.5&&y>=overlay[1]-.5&&y<=overlay[3]+.5&&
   Math.min(Math.abs(x-overlay[0]),Math.abs(x-overlay[2]),Math.abs(y-overlay[1]),Math.abs(y-overlay[3]))<.5;
 }
 const inset={left:card[0],bottom:m.height-card[3]};
 const edge=12*(parseFloat(getComputedStyle(root).getPropertyValue('--content-scale'))||1)+1;
 return {cardInside:inside(card),cardInset:inset,cardAtCorner:inset.left>=-1&&inset.left<=edge&&inset.bottom>=-1&&inset.bottom<=edge,attributionInside:credits.length>0&&credits.every(inside),attributionClear:credits.length>0&&credits.every(c=>!hit(card,c)),
  attributionTight:[...root.querySelectorAll('.map__attribution')].every(n=>getComputedStyle(n).display==='inline')&&getComputedStyle(root.querySelector('[data-poc-sources]')).backgroundColor==='rgba(0, 0, 0, 0)',
  portFactVisible:!!root.querySelector('[data-poc-port-fact]')&&root.querySelector('[data-poc-port-fact]').getBoundingClientRect().height>0,
  spotlightInside:!overlay||inside(overlay),spotlightClear:!overlay||(!fixed.some(b=>hit(overlay,b))&&(!featured||!hit(overlay,featured.box))),
  spotlightConnected,spotlightVisible:!!overlay,
  spotlightInverted:!focusId||!!(overlay&&overlayNode.classList.contains('inverse')&&getComputedStyle(overlayNode).backgroundColor!==getComputedStyle(overlayNode.querySelector('.title')).color),
  spotlightTextConsistent:!overlay||(()=>{const styles=[...overlayNode.querySelectorAll('.label')].map(n=>getComputedStyle(n));return styles.length>0&&styles.every(s=>s.fontSize===styles[0].fontSize&&s.fontFamily===styles[0].fontFamily)&&parseFloat(getComputedStyle(overlayNode.querySelector('.title')).fontSize)>parseFloat(styles[0].fontSize);})(),
  spotlightConnectorWidth:connector?parseFloat(getComputedStyle(connector).strokeWidth):0,
  spotlightSurface:overlay?getComputedStyle(overlayNode).backgroundColor:null,
  spotlightTextColor:overlay?getComputedStyle(overlayNode.querySelector('.title')).color:null,
  spotlightTextVisible:!focusId||!!(overlay&&overlayNode.innerText.trim().length>12&&overlayNode.querySelector('.title')?.innerText.trim().length>=3&&[...overlayNode.children].filter(n=>n.textContent.trim()&&n.getBoundingClientRect().height>0).length>=3),occludedBySpotlight:overlay?ships.filter(s=>hit(s.box,overlay)).length:0,
  hiddenShips:ships.filter(s=>fixed.some(b=>hit(s.box,b))).length,
  maxProjectionError,labelCollisions,leaderCollisions,
  labelRoutes:root.querySelectorAll('.poc__label-route').length,
  labelContentsValid:[...root.querySelectorAll('.poc__label')].every(n=>{const v=[...root.querySelectorAll('.poc__data li')].find(v=>v.dataset.id===n.dataset.id);return v&&n.querySelector('.font--bold')?.textContent===v.dataset.name&&(!n.querySelector('.poc__label-route')||n.querySelector('.poc__label-route').textContent===v.dataset.voyage)&&getComputedStyle(n).backgroundColor===getComputedStyle(root.querySelector('[data-poc-box]')).backgroundColor;}),
  labelsOutside:labels.filter(b=>!inside(b)).length,labels:labels.length,
  leaders:root.querySelectorAll('.poc__leader').length,
  textOverflow:[...root.querySelectorAll('[data-poc-box] > span,[data-poc-spotlight] > span,[data-poc-details] > span,[data-poc-highlights] > span')].filter(n=>n.offsetWidth&&n.scrollWidth>n.clientWidth+2).length};
}
