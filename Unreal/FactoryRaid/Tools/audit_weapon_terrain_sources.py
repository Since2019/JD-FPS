import os,json
from PIL import Image
import numpy as np
T=os.path.dirname(__file__);data=[]
for asset in json.load(open(os.path.join(T,'WeaponTerrainSource','manifest.json'))):
 out={'id':asset['id'],'textures':{}}
 for ch,f in asset['files'].items():
  if ch=='mesh':continue
  with Image.open(f['path']) as im:
   size=im.size;a=np.asarray(im)[::8,::8].astype(float);d={'size':size}
   if 'rough' in ch.lower():d['channel0_quantiles_5_50_95']=list(np.quantile(a[:,:,0] if a.ndim==3 else a,[.05,.5,.95])/255)
   out['textures'][ch]=d
 data.append(out)
open(os.path.join(T,'weapon_terrain_texture_audit.json'),'w').write(json.dumps(data,indent=2))

