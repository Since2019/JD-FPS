"""Original FAST-style helmet art: no functional/manufacturing specifications."""
import os,math
T=os.path.join(os.path.dirname(__file__),'Visual4Source');os.makedirs(T,exist_ok=True)
V=[];F=[]
def vert(p):V.append(p);return len(V)
def face(*p):F.append(p)
def rounded(c,s,p=.35,rings=8,sectors=16):
    def sp(v):return math.copysign(abs(v)**p,v)
    rows=[]
    for j in range(rings+1):
        a=-math.pi/2+math.pi*j/rings
        rows.append([vert((c[0]+s[0]/2*sp(math.cos(a))*sp(math.cos(b)),c[1]+s[1]/2*sp(math.cos(a))*sp(math.sin(b)),c[2]+s[2]/2*sp(math.sin(a)))) for b in [i*math.tau/sectors for i in range(sectors)]])
    for a,b in zip(rows,rows[1:]):
        for i in range(sectors):face(a[i],a[(i+1)%sectors],b[(i+1)%sectors],b[i])
def tube(a,b,r):
    d=[b[i]-a[i] for i in range(3)];ln=sum(v*v for v in d)**.5;d=[v/ln for v in d]
    q=[-d[1],d[0],0]
    if sum(v*v for v in q)<.001:q=[1,0,0]
    ln=sum(v*v for v in q)**.5;q=[v/ln for v in q];n=[d[1]*q[2]-d[2]*q[1],d[2]*q[0]-d[0]*q[2],d[0]*q[1]-d[1]*q[0]]
    rows=[[vert(tuple(c[k]+r*(math.cos(i*math.tau/12)*q[k]+math.sin(i*math.tau/12)*n[k]) for k in range(3))) for i in range(12)] for c in [a,b]]
    for i in range(12):face(rows[0][i],rows[0][(i+1)%12],rows[1][(i+1)%12],rows[1][i])
def save(name):
    with open(os.path.join(T,name+'.obj'),'w') as f:
        f.write('# Original FAST-inspired game mesh\ns 1\n')
        for x,y,z in V:f.write('v %.5f %.5f %.5f\n'%(x,-y,z))
        for x,y,z in V:f.write('vt %.5f %.5f\n'%(y/24,z/24))
        for p in F:f.write('f '+' '.join('%d/%d'%(i,i) for i in reversed(p))+'\n')
    V.clear();F.clear()
shell=[]
for inside in [False,True]:
    rows=[];r=12.4-(.65 if inside else 0)
    for j in range(21):
        row=[]
        for i in range(64):
            a=i*math.tau/64;limit=1.65-.36*abs(math.sin(a))-.08*math.cos(a);t=.012+(limit-.012)*j/20
            row.append(vert((r*math.sin(t)*math.cos(a),r*.88*math.sin(t)*math.sin(a),r*.93*math.cos(t))))
        rows.append(row)
    shell.append(rows)
    for a,b in zip(rows,rows[1:]):
        for i in range(64):face(*(tuple(reversed((a[i],a[(i+1)%64],b[(i+1)%64],b[i]))) if not inside else (a[i],a[(i+1)%64],b[(i+1)%64],b[i])))
for i in range(64):face(shell[0][-1][i],shell[1][-1][i],shell[1][-1][(i+1)%64],shell[0][-1][(i+1)%64])
save('FAST_Shell')
# Open NVG shroud and two segmented ARC-style accessory rails.
for y in [-2.2,2.2]:rounded((11.4,y,3.7),(1.1,1.,5.5))
for z in [1.1,6.1]:rounded((11.4,0,z),(1.1,5.5,1.))
rounded((11.8,0,2.0),(1.8,2.8,1.1))
for side in [-1,1]:
    for x,z in [(-8,1.2),(-5,2.4),(-2,3.1),(1,3.3),(4,3.)]:
        rounded((x,side*(9.5 if abs(x)>5 else 10.5),z),(3.7,1.1,1.6),.22)
        rounded((x,side*11.,z+.85),(1.8,1.2,.4),.2)
    for x in [-7,3.5]:rounded((x,side*10.6,2.9),(1.2,.6,1.2),.8)
save('FAST_Hardware')
# Loop fields, top IFF patch and rear counterweight pouch.
rounded((0,0,11.45),(8,5,.5),.35)
for side in [-1,1]:
    rounded((-3.5,side*8.9,7.0),(5.8,.6,3.0),.4)
rounded((-11.5,0,2),(3.2,7.4,5.4),.5)
save('FAST_Loop')
# Bungee cords connect front mount to the side attachments; four point retention.
for side in [-1,1]:
    tube((11.8,side*2.3,2.1),(8.,side*7.5,2.0),.15)
    tube((8.,side*7.5,2.0),(4.,side*10.7,2.9),.15)
    tube((5.5,side*9.4,0),(5.5,side*8,-8),.4)
    tube((-7.,side*8.7,-1),(5.5,side*8,-8),.4)
    tube((5.5,side*8,-8),(9,side*2.2,-11),.4)
rounded((9,0,-11),(2.3,5.,1.),.4)
save('FAST_Straps')
print('FAST-style shell, rails/shroud, loop panels and retention generated')
