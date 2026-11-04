import pngjs from 'pngjs';
const {PNG}=pngjs;
export function previewPixels(buffer) {
 const png=PNG.sync.read(buffer);let ink=0;
 for(let i=0;i<png.data.length;i+=4) {
  if(png.data[i+3]>0&&Math.min(png.data[i],png.data[i+1],png.data[i+2])<240)ink++;
 }
 const inkFraction=ink/(png.width*png.height);
 if(inkFraction<.001)throw new Error('Blank preview: '+inkFraction+' ink fraction');
 return {width:png.width,height:png.height,inkFraction};
}
