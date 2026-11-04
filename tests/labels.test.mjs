import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const source=await readFile('shared.liquid','utf8');
const window={};vm.runInNewContext(source.match(/<script data-poc-label-engine>([\s\S]*?)<\/script>/)[1],{window});
const labels=window.PortOfCallLabels;
function opts(extra={}){const icon=[90,90,110,110];return {x:100,y:100,icon,width:60,height:16,W:300,H:200,boxes:[icon],lines:[],scale:1,...extra};}
test('nearby labels do not need a leader',()=>{
 const o=opts(),p=labels.plan(o);assert.ok(p);assert.equal(p.line,null);assert.ok(!labels.overlaps(p.rect,o.icon));
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
