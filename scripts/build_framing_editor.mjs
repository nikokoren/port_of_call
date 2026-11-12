// Static, local-draft-only editor. Never changes the live harbor registry.
import {readFile,writeFile,mkdir,cp} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {render} from './render.mjs';
const harbors=JSON.parse(await readFile('port_of_call/harbors.json','utf8')).filter(p=>p.verified);
const landmarks=JSON.parse(await readFile('docs/landmark-sources.json','utf8')).landmarks;
const review=JSON.parse(await readFile('docs/port-fact-poi-review.json','utf8')).facts;
const facts=Object.fromEntries(harbors.map(p=>[p.id,review.filter(f=>f.fact_id.startsWith(p.id+':'))]));
const markup={};
for(const port of harbors){
 const html=await render('full',{port,viewport:port.bbox,camera:{center:port.focus||port.center,zoom:port.zoom??11},status:'ok',message:'',total:0,vessels:[],landmarks:[],source:'Map preview',port_fact:{text:facts[port.id][0].text}},{port_facts:true});
 markup[port.id]=html.replaceAll('https://trmnl.com/js/maplibre-gl/5.24.0/','assets/').replace(/data-poc-count>[^<]*/,'data-editor-count>Map framing preview');
}
const dest='site/framing';await mkdir(dest+'/assets',{recursive:true});
for(const name of ['index.html','editor.css','editor.mjs','bridge.mjs','draft.mjs'])await cp('editor/'+name,dest+'/'+name);
for(const name of ['plugins.js','maplibre-gl.js','maplibre-gl.css'])await cp('var/assets/'+name,dest+'/assets/'+name);
const css=(await readFile('var/assets/plugins.css','utf8')).replaceAll('/fonts/','fonts/');await writeFile(dest+'/assets/plugins.css',css);
await cp('var/assets/fonts',dest+'/assets/fonts',{recursive:true});
await cp('var/assets/licenses',dest+'/licenses',{recursive:true});
const revision=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim();
await writeFile(dest+'/data.json',JSON.stringify({revision,harbors,landmarks:Object.fromEntries(harbors.map(p=>[p.id,landmarks[p.id]])),facts,markup}));
console.log(`Built framing editor for ${harbors.length} harbors / ${Object.values(landmarks).flat().length} POIs; live registry unchanged.`);
