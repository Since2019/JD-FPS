"""Create centimetre-scale terrain geometry from licensed source height maps."""
import os,json,math
import numpy as np
from PIL import Image
T=os.path.dirname(__file__);D=os.path.join(T,'WeaponTerrainSource');items={i['id']:i for i in json.load(open(os.path.join(D,'manifest.json')))}
def heights(name):
 a=np.asarray(Image.open(items[name]['files']['Displacement']['path']),dtype=float)
 if a.ndim==3:a=a[:,:,0]
 lo,hi=float(a.min()),float(a.max());return (a-lo)/max(1.,hi-lo)
def sample(a,u,v):return float(a[min(a.shape[0]-1,max(0,int(v*(a.shape[0]-1)))),min(a.shape[1]-1,max(0,int(u*(a.shape[1]-1))))])
def write(name,verts,uv,faces):
 with open(os.path.join(D,name+'.obj'),'w') as f:
  f.write('# Source-height-derived geometry; centimetres; height amplitude is project estimate\ns 1\n')
  for x,y,z in verts:f.write('v %.6f %.6f %.6f\n'%(x,-y,z))
  for u,v in uv:f.write('vt %.6f %.6f\n'%(u,v))
  for face in faces:f.write('f '+' '.join('%d/%d'%(i+1,i+1) for i in reversed(face))+'\n')
a=heights('snow_field_aerial');N=129;verts=[];uv=[];faces=[]
for y in range(N):
 for x in range(N):
  u=x/(N-1);v=y/(N-1);verts.append(((u-.5)*8000,v*8000,(sample(a,u,v)-.5)*100));uv.append((u,1-v))
for y in range(N-1):
 for x in range(N-1):i=y*N+x;faces.extend([(i,i+1,i+N),(i+1,i+N+1,i+N)])
write('SM_ScannedSnowField',verts,uv,faces)
a=heights('snow_02');R=16;S=64;verts=[(0,0,10)];uv=[(.5,.5)];faces=[]
for r in range(1,R+1):
 for k in range(S):
  t=math.tau*k/S;q=r/R;x=160*q*math.cos(t);y=40*q*math.sin(t);u=x/200+.5;v=y/200+.5;verts.append((x,y,(2+10*sample(a,u,v))*(1-q**4)));uv.append((u,1-v))
for k in range(S):faces.append((0,1+k,1+(k+1)%S))
for r in range(R-1):
 for k in range(S):
  i=1+r*S+k;j=1+r*S+(k+1)%S;faces.extend([(i,i+S,j),(j,i+S,j+S)])
write('SM_ScannedSnowDrift',verts,uv,faces)
open(os.path.join(D,'height_mesh_notes.json'),'w').write(json.dumps({'snowfield_cm':[8000,8000,100],'snowfield_tris':32768,'snowdrift_cm':[320,80,12],'snowdrift_tris':len(faces),'height_amplitudes':'Project estimates, not recovered real-world absolute elevations','horizontal_scale':'Aerial field 80 m from Poly Haven metadata; deck drift authored 3.2 x .8 m'},indent=2))

