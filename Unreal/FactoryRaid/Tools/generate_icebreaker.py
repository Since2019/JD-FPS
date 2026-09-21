"""Original icebreaker hull and pack-ice meshes, centimetres, not a real vessel replica."""
import os, math
T=os.path.join(os.path.dirname(__file__),'IcebreakerSource');os.makedirs(T,exist_ok=True)
def write(name,verts,faces):
    with open(os.path.join(T,name+'.obj'),'w') as f:
        f.write('# Original Icebreaker environment geometry\ns 1\n')
        for x,y,z in verts:f.write('v %.5f %.5f %.5f\n'%(x,-y,z))
        for x,y,z in verts:f.write('vt %.5f %.5f\n'%(x/200,z/200))
        for face in faces:f.write('f '+' '.join('%d/%d'%(i+1,i+1) for i in reversed(face))+'\n')
# Rounded stern, parallel working body and a broad sloping icebreaking bow.
stations=[(-4000,480),(-3900,710),(-3650,830),(-3200,870),(-2400,890),(-1200,890),(0,880),(1200,850),(2300,760),(3000,610),(3500,400),(3900,130),(4000,1)]
verts=[];faces=[]
for x,w in stations:
    for z,scale in [(70,1),(0,1),(-180,.94),(-390,.73),(-570,.38)]:
        verts.extend([(x,w*scale,z),(x,-w*scale,z)])
for j in range(len(stations)-1):
    for k in range(4):
        for side in [0,1]:
            a=j*10+k*2+side;b=(j+1)*10+k*2+side
            faces.append((a,b,b+2,a+2) if side==0 else (a+2,b+2,b,a))
    faces.append((j*10+8,(j+1)*10+8,(j+1)*10+9,j*10+9))
faces.extend([(0,1,3,5,7,9,8,6,4,2),(120,122,124,126,128,129,127,125,123,121)])
write('SM_IcebreakerHull',verts,faces)
verts=[];faces=[]
for x,w in stations:verts.extend([(x,-w,0),(x,w,0),(x,-w,-16),(x,w,-16)])
for j in range(len(stations)-1):
    a=j*4;b=(j+1)*4
    faces.extend([(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)])
faces.extend([(0,1,3,2),(48,50,51,49)])
write('SM_Deck',verts,faces)
verts=[];faces=[]
for z,scale in [(0,1),(-35,.8)]:
    for i in range(9):
        angle=i*math.tau/9;r=(.8+.2*math.sin(i*13.4))*scale
        verts.append((math.cos(angle)*100*r,math.sin(angle)*100*r,z))
faces.append(tuple(range(9)));faces.append(tuple(reversed(range(9,18))))
for i in range(9):faces.append((i,(i+1)%9,(i+1)%9+9,i+9))
write('SM_IceFloe',verts,faces)
print('Icebreaker hull, deck and ice geometry generated')
