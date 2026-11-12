import test from 'node:test';
import assert from 'node:assert/strict';
import {DRAFT_KIND,cameraFor,zoomValue,validateDraft,setCamera,draftHash,readDraftHash} from '../editor/draft.mjs';
const port={id:'seattle',focus:[-122.38083,47.63245],center:[-122.3,47.6],zoom:12};
const fresh=()=>({kind:DRAFT_KIND,schema_version:1,base_revision:'reviewed-source',harbors:{}});
test('framing draft keeps OG and X independent and resets only the chosen view',()=>{
 const draft=fresh();setCamera(draft,port,'og',{focus:[-122.4,47.65],zoom:11});
 assert.deepEqual(cameraFor(port,draft,'x'),{focus:port.focus,zoom:12});
 setCamera(draft,port,'x',{focus:[-122.41,47.66],zoom:11.25});
 setCamera(draft,port,'og',{focus:port.focus,zoom:12});
 assert.ok(!draft.harbors.seattle.og);assert.equal(draft.harbors.seattle.x.zoom,11.25);
});
test('framing zoom follows whole steps by default and explicit quarter steps with decimal commas',()=>{
 assert.equal(zoomValue(10.5),11);assert.equal(zoomValue('11,25',true),11.25);assert.equal(zoomValue('10.5',true),10.5);
 for(const bad of ['', 'no',Infinity,-1,21])assert.throws(()=>zoomValue(bad));
});
test('draft links round-trip the exact reviewed cameras',()=>{
 const draft=fresh();setCamera(draft,port,'og',{focus:[-122.405672,47.642568],zoom:10.5});
 assert.deepEqual(readDraftHash('#draft='+draftHash(draft),[port]),draft);
});
test('untrusted imports reject unknown ports, devices, coordinates and malformed data',()=>{
 for(const harbors of [{unknown:{og:{focus:port.focus,zoom:12}}},{seattle:{phone:{focus:port.focus,zoom:12}}},{seattle:{og:{focus:[0,90],zoom:12}}},{seattle:{og:{focus:[0,0],zoom:11.1}}},{seattle:{og:{focus:['0',0],zoom:12}}}])assert.throws(()=>validateDraft({...fresh(),harbors},[port]));
 assert.throws(()=>readDraftHash('#draft=bad',[port]));
});
