"""Original MK18-style game meshes, not manufacturing geometry. UE centimetres, +Y forward."""
import os,math
T=os.path.join(os.path.dirname(__file__),'WeaponSource');os.makedirs(T,exist_ok=True)
V=[];F=[]
def v(p):V.append(p);return len(V)
def face(*p):F.append(p)
def rounded(c,s,p=.22,rings=8,sectors=16):
    def sp(a):return math.copysign(abs(a)**p,a)
    rows=[]
    for j in range(rings+1):
        a=-math.pi/2+math.pi*j/rings
        rows.append([v((c[0]+s[0]/2*sp(math.cos(a))*sp(math.cos(b)),c[1]+s[1]/2*sp(math.cos(a))*sp(math.sin(b)),c[2]+s[2]/2*sp(math.sin(a)))) for b in [i*math.tau/sectors for i in range(sectors)]])
    for j in range(rings):
        for i in range(sectors):face(rows[j][i],rows[j][(i+1)%sectors],rows[j+1][(i+1)%sectors],rows[j+1][i])
def prism(profile,width,x=0):
    a=[v((x-width/2,y,z)) for y,z in profile];b=[v((x+width/2,y,z)) for y,z in profile]
    face(*reversed(a));face(*b)
    for i in range(len(a)):face(a[i],a[(i+1)%len(a)],b[(i+1)%len(a)],b[i])
def tube(y0,y1,r,inner=0,z=10,x=0):
    rows=[]
    for y,rad in [(y0,r),(y1,r),(y1,inner),(y0,inner)]:rows.append([v((x+rad*math.cos(i*math.tau/32),y,z+rad*math.sin(i*math.tau/32))) for i in range(32)])
    for a,b in zip(rows,rows[1:]+rows[:1]):
        for i in range(32):face(a[i],a[(i+1)%32],b[(i+1)%32],b[i])
def save(name):
    uv=[];faces=[]
    for poly in F:
        pts=[V[i-1] for i in poly];a,b,c=pts[:3];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)];n=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]];axis=max(range(3),key=lambda i:abs(n[i]));axes=[i for i in range(3) if i!=axis];out=[]
        for index,point in zip(poly,pts):uv.append((point[axes[0]]/20,point[axes[1]]/20));out.append((index,len(uv)))
        faces.append(out)
    with open(os.path.join(T,name+'.obj'),'w') as f:
        f.write('# Authored game-art mesh\ns 1\n')
        for x,y,z in V:f.write('v %.6f %.6f %.6f\n'%(x,-y,z))
        for x,y in uv:f.write('vt %.6f %.6f\n'%(x,y))
        for poly in faces:f.write('f '+' '.join('%d/%d'%pair for pair in reversed(poly))+'\n')
    V.clear();F.clear()

# Forged upper/lower receiver silhouette, magazine well, charging-handle wings.
prism([(-7,8),(-6,12.4),(-3,13),(17,13),(20,11.3),(20,7),(13,5.8),(8,5.8),(7,3),(0,3),(-1,5),(-6,6)],4.4)
rounded((0,5,11.6),(4.9,21.5,2.6),.6)
prism([(8.2,6.9),(17,6.9),(17.6,1.0),(10,.3)],5.0)
rounded((0,-6.2,12.3),(7.0,1.4,.7),.22)
for y in range(-5,20):rounded((0,y,13.4),(5.2,.5,.5),.16,rings=4,sectors=8)
save('MK18_Receiver')

# Ventilated RIS-II-style quad rail cage and closely spaced Picatinny lugs.
for x in [-1.6,1.6]:
    for z in [7.5,12.5]:rounded((x,31.5,z),(.8,24,1.0),.2)
for x in [-2.35,2.35]:
    for z in [8,12]:rounded((x,31.5,z),(.4,24,.7),.2)
    for y in [20.2+i*2.2 for i in range(11)]:rounded((x,y,10),(.4,.65,3.4),.22)
for y in [20+i*1.02 for i in range(24)]:
    for z in [6.8,13.4]:rounded((0,y,z),(4.6,.53,.6),.17,rings=4,sectors=8)
    for x in [-2.85,2.85]:rounded((x,y,10),(.6,.53,3.5),.17,rings=4,sectors=8)
for y in [19.5,43.5]:
    for x in [-2.4,2.4]:rounded((x,y,10),(.6,1.2,5),.2)
save('MK18_RIS')

# Short exposed barrel, open flash-hider crown, buffer tube and receiver controls.
tube(19.2,47.5,.85,z=10);tube(43.6,44.5,1.05,z=10)
tube(47,50,1.15,.64,z=10)
for a in [i*math.tau/5 for i in range(5)]:
    rounded((.96*math.cos(a),50.6,10+.96*math.sin(a)),(.42,1.8,.42),.4)
tube(-29,-6,1.45,z=9.8)
rounded((2.3,5,10),( .22,9.4,2.6),.3)
rounded((2.53,5,8.5),(.25,9.6,.6),.3)
rounded((2.6,-3,9.8),(1.4,2.0,1.4),.55)
for x in [-2.7,2.7]:
    for y,z in [(-4,6),(6,4),(18,11),(20.1,8.5),(20.1,11.6)]:rounded((x,y,z),(.3,.65,.65),.75,rings=6,sectors=12)
rounded((-2.5,.5,6.3),(.65,2.2,.45),.4)
rounded((2.6,7.7,4.8),(.45,1.8,.75),.35)
# Trigger guard frame stays hollow, rather than a solid block around the hand.
rounded((0,3.6,.1),(1.0,7.2,.65),.25)
for y in [.2,7.]:rounded((0,y,1.8),(1.,.6,3.4),.3)
prism([(3.6,3.2),(3.3,2.1),(3.7,1),(4.3,.8),(4.0,2.3),(4.2,3.2)],.4)
save('MK18_Hardware')

# Collapsible shoulder stock, pistol grip and curved thirty-round silhouette.
prism([(-31,13),(-22,13),(-17,10.8),(-17,7.6),(-23,6.4),(-25,-.2),(-31,-.2)],5.3)
for x in [-3,3]:rounded((x,-26,11.1),(2.4,9.,3.3),.45)
rounded((0,-22.5,5.8),(3.1,6,.9),.25)
prism([(-2,4),(2,3),(0,-7),(-4,-7.8),(-5.2,-5.8)],3.6)
prism([(10.6,1.4),(16.8,2.0),(18,-4.2),(20.4,-12.1),(18.5,-14.0),(12.7,-12.3),(11.4,-5)],3.9)
for x in [-2.05,2.05]:
    for y in [12.1,14.3,16.4]:prism([(y,-1.5),(y+.4,-1.5),(y+2.2,-11),(y+1.8,-11)],.25,x=x)
for z in [-6,-4,-2,0]:rounded((0,-2.0+z*.24,z),(3.7,.45,.35),.4)
save('MK18_Polymer')
rounded((0,-31.2,6.4),(5.4,1.1,13.8),.3)
for z in [1+i*.7 for i in range(16)]:rounded((0,-31.85,z),(4.3,.15,.20),.35,rings=4,sectors=8)
rounded((2.48,5,10),(.08,8.3,1.7),.2)
save('MK18_Dark')

# Proper cylindrical UVs for cloth: previous unit-mesh planar UVs collapsed after scaling.
sectors=48;rings=32;rows=[];uv=[]
for j in range(rings+1):
    t=j/rings;row=[]
    for i in range(sectors+1):
        a=i*math.tau/sectors;r=.80+.15*math.sin(math.pi*t)-.12*t+.025*math.sin(t*39+math.sin(a*3)*2)+.016*math.sin(t*81+a*5)
        row.append(v((r*math.cos(a),r*.9*math.sin(a),t-.5)));uv.append((i/sectors,t))
    rows.append(row)
for j in range(rings):
    for i in range(sectors):face(rows[j][i],rows[j][i+1],rows[j+1][i+1],rows[j+1][i])
with open(os.path.join(T,'PMC_ClothUV.obj'),'w') as f:
    f.write('s 1\n')
    for x,y,z in V:f.write('v %f %f %f\n'%(x,-y,z))
    for x,y in uv:f.write('vt %f %f\n'%(x,y))
    for poly in F:f.write('f '+' '.join('%d/%d'%(i,i) for i in reversed(poly))+'\n')
print('MK18-style geometry and cloth UV mesh generated')
