import test from 'node:test';
import assert from 'node:assert/strict';
import pngjs from 'pngjs';
import {previewPixels} from '../scripts/preview-pixels.mjs';
const {PNG}=pngjs;
test('a geometrically valid but blank preview is rejected',()=>{
 const png=new PNG({width:10,height:10});png.data.fill(255);
 assert.throws(()=>previewPixels(PNG.sync.write(png)),/Blank preview/);
 for(let i=0;i<200;i+=4)png.data[i]=png.data[i+1]=png.data[i+2]=0;
 assert.equal(previewPixels(PNG.sync.write(png)).inkFraction,.5);
});
