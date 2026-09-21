"""Authored optic housing, lens surface and PMC construction details, centimetres."""
import math,os
import generate_presentation_assets as g

def ring(y,radius,inner,length,z=22):
    rows=[]
    for yy,rr in [(y,radius),(y+length,radius),(y+length,inner),(y,inner)]:
        rows.append([g.vertex((rr*math.cos(i*math.tau/64),yy,z+rr*math.sin(i*math.tau/64))) for i in range(64)])
    for a,b in zip(rows,rows[1:]+rows[:1]):
        for i in range(64):g.face(a[i],a[(i+1)%64],b[(i+1)%64],b[i])

# Hollow optical housing: no opaque block through the view.
ring(-.5,2.55,2.05,1.5);ring(1.,2.35,2.05,12.8);ring(13.8,2.65,2.05,1.5)
g.rounded((0,7.2,18.8),(4.5,11.5,2.4),.28)
for y in [3,10.5]:g.rounded((0,y,17.2),(5.1,1.6,1.0),.25)
g.rounded((-3.0,5.,21.2),(2.,3.2,3.2),.40)
g.rounded((2.8,9.,19.4),(1.2,3.,2.2),.25)
g.save('OPT_Housing')
for y in [-.2,.2,.6,14.,14.4,14.8]:ring(y,2.60 if y<1 else 2.7,2.52 if y<1 else 2.62,.12)
for x in [-2.2,2.2]:
    for y in [3,10.5]:g.rounded((x,y,17.4),(.45,.9,.9),.65)
g.rounded((-3.9,5,21.2),(.20,2.3,2.3),.55)
g.rounded((3.1,6.5,18.2),(.45,6.,.65),.28)
g.save('OPT_Hardware')
# Lens quad is mapped explicitly; masked reticle is etched in this 3D plane.
p=os.path.join(g.ROOT,'OPT_Reticle.obj')
with open(p,'w') as f:
    f.write('s 1\n')
    for x,z in [(-2.04,19.96),(2.04,19.96),(2.04,24.04),(-2.04,24.04)]:f.write('v %f -0.08 %f\n'%(x,z))
    f.write('vt 0 1\nvt 1 1\nvt 1 0\nvt 0 0\nf 1/1 2/2 3/3 4/4\n')

# Plate-carrier seams, individual shoulder straps and restrained exposed hardware.
for y in [-15.3,15.3]:
    g.rounded((12.9,y,0),(.40,.48,33),.5,rings=6,sectors=10)
    g.rounded((4,y,21),(19,4.,1.8),.4)
for z in [-17.2,17.2]:g.rounded((12.9,0,z),(.4,29,.45),.5,rings=6,sectors=10)
for y in [-11,-3.6,3.6,11]:
    g.rounded((18.25,y,-6),(.28,.35,12),.5,rings=6,sectors=10)
g.save('PMC_Seams')
for y in [-14.5,14.5]:
    g.rounded((12.8,y,16),(1.8,4.5,5),.25)
    g.rounded((13.8,y,16),(.6,2.6,2.7),.35)
    g.rounded((13.4,y,-13),(1.,3.,2.3),.35)
g.save('PMC_Buckles')
g.rounded((0,0,0),(4.5,6,12),.28)
g.rounded((0,0,7),(2.5,4,2),.28)
g.rounded((0,1.4,17),(.45,.45,19),.7,rings=12,sectors=12)
g.save('PMC_Radio')
g.rounded((0,0,0),(6,9,13),.4)
g.rounded((3.2,0,2),(.6,7.5,2),.3)
g.save('PMC_UtilityPouch')
for z in [-3,0,3]:g.rounded((0,0,z),(1.0,8.,.45),.5,rings=6,sectors=12)
g.save('PMC_Zipper')
# Tapered cloth volumes with asymmetric folds instead of inflated oval sleeves.
rows=[];sectors=32;rings=28
for j in range(rings+1):
    t=j/rings;row=[]
    taper=.78+.16*math.sin(math.pi*t)-.13*t
    for i in range(sectors):
        a=i*math.tau/sectors
        fold=.03*math.sin(t*39+math.sin(a*3)*2)+.018*math.sin(t*81+a*5)
        r=taper+fold
        row.append(g.vertex((r*math.cos(a),r*.90*math.sin(a),t-.5)))
    rows.append(row)
for j in range(rings):
    for i in range(sectors):g.face(rows[j][i],rows[j][(i+1)%sectors],rows[j+1][(i+1)%sectors],rows[j+1][i])
g.face(*reversed(rows[0]));g.face(*rows[-1]);g.save('PMC_FabricLimb')
print('Optic and detailed PMC source meshes ready')
