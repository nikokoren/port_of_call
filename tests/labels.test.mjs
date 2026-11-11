import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const source=await readFile('shared.liquid','utf8');
const window={};vm.runInNewContext(source.match(/<script data-poc-label-engine>([\s\S]*?)<\/script>/)[1],{window});
const labels=window.PortOfCallLabels;
test('count text separates its divider and keeps the shown count together',()=>{
 assert.equal(labels.countCopy(322,19),'322 vessels in area ·\u00a019\u00a0on\u00a0map');
 assert.equal(labels.countCopy(19,19),'19 vessels in area');
 assert.equal(labels.countCopy(0,0),'0 vessels in area');
});
test('voyage shortening preserves the destination and bidirectional meaning',()=>{
 const direct=labels.voyageChoices('Hanko, FI → Tilbury, GB');
 assert.ok(direct.includes('Hanko, FI → Tilbury, GB'));assert.ok(direct.includes('To Tilbury, GB'));
 const route=labels.voyageChoices('Route: Southworth ↔ Seattle, USA');
 assert.ok(route.includes('Southworth ↔ Seattle, USA'));assert.ok(route.every(s=>!s.startsWith('To ')));
});
function opts(extra={}){const icon=[90,90,110,110];return {x:100,y:100,icon,width:60,height:16,W:300,H:200,boxes:[icon],lines:[],scale:1,...extra};}
test('every label, even one beside its ship, has a visible leader to it',()=>{
 const o=opts(),p=labels.plan(o);assert.ok(p);assert.ok(!labels.overlaps(p.rect,o.icon));
 assert.ok(p.line,'adjacent label has a leader');
 const [x1,y1,x2,y2]=p.line;assert.ok(Math.hypot(x2-x1,y2-y1)>=8*o.scale,'leader is long enough to see');
 // It starts at the ship icon's edge and ends at the label.
 assert.ok(x1>=o.icon[0]-.01&&x1<=o.icon[2]+.01&&y1>=o.icon[1]-.01&&y1<=o.icon[3]+.01);
 assert.ok(x2>=p.rect[0]-.01&&x2<=p.rect[2]+.01&&y2>=p.rect[1]-.01&&y2<=p.rect[3]+.01);
});
test('blocked adjacent positions use a leader without crossing other ships',()=>{
 const o=opts();o.boxes.push([113,95,125,105],[75,95,87,105],[95,75,105,87],[95,113,105,125]);
 const p=labels.plan(o);assert.ok(p?.line,'a displaced label needs a leader');
 assert.ok(!o.boxes.some(b=>labels.overlaps(p.rect,b)));
 assert.ok(!labels.lineHits(p.line,o.boxes.filter(b=>b!==o.icon)));
});
test('overlays and attribution reserve space for labels and leader lines',()=>{
 const o=opts();o.boxes.push([0,0,89,200],[0,160,300,200],[170,0,300,200]);
 const p=labels.plan(o);assert.ok(p);
 assert.ok(!o.boxes.some(b=>labels.overlaps(p.rect,b)));
 if(p.line)assert.ok(!labels.lineHits(p.line,o.boxes.filter(b=>b!==o.icon)));
 assert.equal(labels.plan(opts({boxes:[[0,0,300,200]]})),null);
});
test('new labels cannot cover an existing leader',()=>{
 const o=opts({lines:[[100,100,200,100]]}),p=labels.plan(o);
 assert.ok(p);assert.ok(!labels.lineHits(o.lines[0],[p.rect]));
});
test('exact segment checks catch narrow obstacles and ignore distant boxes',()=>{
 assert.equal(labels.lineHits([0,0,100,100],[[50,49,50.1,51]]),true);
 assert.equal(labels.lineHits([0,0,100,100],[[0,80,20,100]]),false);
});
test('placement is deterministic and keeps names inside narrow views',()=>{
 const o=opts({x:12,y:30,icon:[4,20,20,40],W:140,H:100,boxes:[[4,20,20,40]]});
 const p=labels.plan(o);assert.ok(p);assert.deepEqual(p,labels.plan(o));
 assert.ok(p.rect[0]>=0&&p.rect[1]>=0&&p.rect[2]<=140&&p.rect[3]<=100);
});

test('extended ship label always has a connector and avoids fixed overlays',()=>{
 const icon=[270,140,290,160],fixed=[[0,190,180,300],[250,280,400,300]];
 const o={x:280,y:150,icon,width:170,height:95,W:400,H:300,fixed,ships:[],scale:1};
 const p=labels.spotlight(o);assert.ok(p?.line);assert.ok(!labels.overlaps(p.rect,icon));
 assert.ok(fixed.every(b=>!labels.overlaps(p.rect,b)));assert.ok(!labels.lineHits(p.line,fixed));
 assert.deepEqual(p,labels.spotlight(o));
 assert.ok(p.rect[0]>=8&&p.rect[1]>=8&&p.rect[2]<=392&&p.rect[3]<=292);
});
test('other vessels are soft obstacles for the extended label',()=>{
 const o={x:350,y:150,icon:[340,140,360,160],width:170,height:95,W:400,H:300,fixed:[],ships:[[0,0,330,300]],scale:1};
 const p=labels.spotlight(o);assert.ok(p);assert.equal(p.covered,1);
 assert.equal(labels.spotlight({...o,fixed:[[0,0,400,300]]}),null);
});
test('compact extended label can share a view with the independent harbor key',()=>{
 const o={x:280,y:110,icon:[268,95,292,125],width:171,height:84,W:380,H:220,fixed:[[8,116,182,212],[190,200,380,220]],ships:[],scale:1};
 const p=labels.spotlight(o);assert.ok(p?.line);assert.ok(!o.fixed.some(b=>labels.overlaps(p.rect,b)));
});
