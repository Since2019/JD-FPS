"""Original PMC equipment meshes and short foley samples; no external asset download."""
import os,math,json,wave,random,struct
ROOT=os.path.join(os.path.dirname(__file__),'PresentationSource');os.makedirs(ROOT,exist_ok=True)
V=[];F=[]
def reset():V.clear();F.clear()
def vertex(p):V.append(p);return len(V)
def face(*p):F.append(p)
def rounded(center,size,power=.3,rings=12,sectors=24):
    def sp(v):return math.copysign(abs(v)**power,v)
    rows=[]
    for j in range(rings+1):
        a=-math.pi/2+math.pi*j/rings;row=[]
        for i in range(sectors):
            b=2*math.pi*i/sectors
            row.append(vertex((center[0]+size[0]*.5*sp(math.cos(a))*sp(math.cos(b)),center[1]+size[1]*.5*sp(math.cos(a))*sp(math.sin(b)),center[2]+size[2]*.5*sp(math.sin(a)))))
        rows.append(row)
    for j in range(rings):
        for i in range(sectors):face(rows[j][i],rows[j][(i+1)%sectors],rows[j+1][(i+1)%sectors],rows[j+1][i])
def save(name):
    path=os.path.join(ROOT,name+'.obj')
    with open(path,'w') as f:
        f.write('# Original factory PMC equipment, centimetres\ns 1\n')
        # Interchange OBJ is Z-up and flips its right-handed Y axis on import.
        for x,y,z in V:f.write('v %.5f %.5f %.5f\n'%(x,-y,z))
        for x,y,z in V:f.write('vt %.5f %.5f\n'%(y*.035,z*.035))
        for p in F:f.write('f '+' '.join('%d/%d'%(i,i) for i in reversed(p))+'\n')
    reset()

rounded((0,0,0),(25,36,40),.28);save('PMC_Vest')
for y in [-12,-4,4,12]:
    rounded((0,y,0),(6,7,15),.22)
    rounded((3.2,y,5),(1,6,3),.25)
save('PMC_MagPouches')
for z in [-13,-6,1,8,15]:
    for y in [-12,-4,4,12]:rounded((0,y,z),(1,6.5,1.1),.25,rings=6,sectors=12)
save('PMC_Webbing')
rounded((0,0,0),(16,29,38),.36);rounded((-8,0,-5),(4,23,18),.3);save('PMC_Backpack')
rounded((0,0,0),(23,35,7),.2);save('PMC_Belt')
rounded((0,0,0),(20,18,26),.94,rings=18,sectors=32);save('PMC_Balaclava')
# Shell with an inner surface and high ear cutouts.
shell=[];sectors=48;rings=14
for inner in [False,True]:
    rows=[];r=11.7-(.8 if inner else 0)
    for j in range(rings+1):
        row=[]
        for i in range(sectors):
            a=2*math.pi*i/sectors
            limit=1.62-.24*abs(math.sin(a))-.10*math.cos(a)
            t=.025+(limit-.025)*j/rings
            row.append(vertex((r*math.sin(t)*math.cos(a),r*.91*math.sin(t)*math.sin(a),r*.94*math.cos(t))))
        rows.append(row)
    shell.append(rows)
    for j in range(rings):
        for i in range(sectors):
            q=(rows[j][i],rows[j][(i+1)%sectors],rows[j+1][(i+1)%sectors],rows[j+1][i]);face(*(q if inner else tuple(reversed(q))))
for i in range(sectors):face(shell[0][-1][i],shell[1][-1][i],shell[1][-1][(i+1)%sectors],shell[0][-1][(i+1)%sectors])
save('PMC_Helmet')
rounded((0,0,0),(2,17,6),.42);save('PMC_GoggleFrame')
rounded((0,0,0),(1,14.7,3.6),.4);save('PMC_GoggleLens')
for y in [-10.6,10.6]:rounded((0,y,0),(7,3,9),.55)
rounded((10.5,0,4),(2,4.5,5),.3);save('PMC_HeadHardware')
rounded((0,0,0),(4,11,14),.55);save('PMC_Kneepad')
rounded((0,0,0),(1,8,4),.22);save('PMC_Patch')
rounded((0,0,0),(2,2,1),.72,rings=14,sectors=24);save('PMC_FabricLimb')
rounded((0,0,0),(26,12,11),.4);rounded((0,0,-5),(27,12.5,2.5),.25);save('PMC_Boot')

# Foley: band-limited transients, small metal clicks and cloth movement.
sr=44100;rng=random.Random(2891)
def sample(name,duration,kind):
    count=int(sr*duration);raw=[];low=0.
    for i in range(count):
        t=i/sr;n=rng.uniform(-1,1);low=.90*low+.10*n
        if kind=='step':
            s=.43*math.sin(2*math.pi*(85-100*t)*t)*math.exp(-t*27)+.22*low*math.exp(-t*14)+.09*n*math.exp(-t*90)
        elif kind=='cloth':s=.32*low*math.sin(math.pi*t/duration)**2+.04*n*math.exp(-t*30)
        elif kind=='impact':s=.20*n*math.exp(-t*70)+.20*math.sin(2*math.pi*1700*t)*math.exp(-t*45)+.08*math.sin(2*math.pi*670*t)*math.exp(-t*22)
        else:
            s=0.
            for offset in [0.,.10,.19]:
                a=t-offset
                if a>=0:s+=(.13*n+.18*math.sin(2*math.pi*1900*a))*math.exp(-a*110)
        s*=min(1,i/32,max(0,(count-i)/80));raw.append(struct.pack('<h',int(max(-.85,min(.85,s))*32767)))
    with wave.open(os.path.join(ROOT,name+'.wav'),'wb') as out:out.setparams((1,2,sr,0,'NONE','not compressed'));out.writeframes(b''.join(raw))
sample('Step_Concrete',.32,'step');sample('Gear_Cloth',.24,'cloth');sample('Impact_Metal',.22,'impact');sample('Search_Latch',.35,'click')
print(ROOT)
