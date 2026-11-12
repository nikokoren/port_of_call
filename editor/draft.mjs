export const DRAFT_KIND='port-of-call-framing-draft';
export function cameraFor(port,draft,device){return draft.harbors?.[port.id]?.[device]||port.cameras?.[device]||{focus:[...(port.focus||port.center)],zoom:port.zoom??11};}
export function zoomValue(value,fractional=false){
 const raw=String(value).trim().replace(',','.');
 const n=raw?Number(raw):NaN;
 if(!Number.isFinite(n)||n<0||n>20)throw new Error('Choose a zoom between 0 and 20.');
 return Math.round(n*(fractional?4:1))/(fractional?4:1);
}
export function validateDraft(value,ports){
 if(value?.kind!==DRAFT_KIND||value.schema_version!==1||!value.harbors||typeof value.harbors!=='object')throw new Error('This is not a Port of Call framing draft.');
 const known=new Set(ports.map(p=>p.id)),harbors={};
 for(const [id,profiles] of Object.entries(value.harbors)){
  if(!known.has(id))throw new Error('Unknown harbor in draft: '+id);
  const out={};
  for(const [device,c] of Object.entries(profiles)){
   if(!['og','x'].includes(device)||!Array.isArray(c?.focus)||c.focus.length!==2||!c.focus.every(n=>typeof n==='number'&&Number.isFinite(n)))throw new Error('Invalid device or focus for '+id);
   if(Math.abs(c.focus[0])>180||Math.abs(c.focus[1])>85||typeof c.zoom!=='number'||!Number.isFinite(c.zoom)||c.zoom<0||c.zoom>20||Math.abs(c.zoom*4-Math.round(c.zoom*4))>1e-7)throw new Error('Invalid coordinates or quarter-step zoom for '+id);
   out[device]={focus:[...c.focus],zoom:c.zoom};
  }
  if(Object.keys(out).length)harbors[id]=out;
 }
 return{kind:DRAFT_KIND,schema_version:1,base_revision:typeof value.base_revision==='string'?value.base_revision:'',harbors};
}
export function setCamera(draft,port,device,camera){
 const clean={focus:camera.focus.map(n=>Math.round(n*1e6)/1e6),zoom:camera.zoom};
 validateDraft({kind:DRAFT_KIND,schema_version:1,harbors:{[port.id]:{[device]:clean}}},[port]);
 const original=cameraFor(port,{harbors:{}},device),same=clean.zoom===original.zoom&&clean.focus.every((n,i)=>Math.abs(n-original.focus[i])<.000001);
 if(same){if(draft.harbors[port.id]){delete draft.harbors[port.id][device];if(!Object.keys(draft.harbors[port.id]).length)delete draft.harbors[port.id];}}
 else (draft.harbors[port.id]??={})[device]=clean;
 return draft;
}
export function draftHash(draft){const bytes=new TextEncoder().encode(JSON.stringify(draft));return btoa(String.fromCharCode(...bytes)).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');}
export function readDraftHash(hash,ports){const value=hash.replace(/^#draft=/,'');if(value.length>20000)throw new Error('Draft link is too long.');return validateDraft(JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(value.replaceAll('-','+').replaceAll('_','/')),c=>c.charCodeAt(0)))),ports);}
