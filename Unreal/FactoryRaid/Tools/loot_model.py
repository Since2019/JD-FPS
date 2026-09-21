"""Engine-independent grid inventory; transfers are atomic and preserve item identity."""
import itertools
_ids=itertools.count(1)
CATALOG={
    '7.62 栓动步枪':(5,2,4.0,'WEAPON'),
    'HK416':(4,2,3.5,'WEAPON'),
 '医疗包':(2,1,.6,'MED'), '绷带':(1,1,.08,'MED'), '止痛药':(1,1,.05,'MED'),
 '5.56 弹药':(1,1,.36,'AMMO'), 'STANAG 弹匣':(1,2,.48,'AMMO'),
 'MK18 风格步枪':(4,2,2.9,'WEAPON'), 'FAST 风格头盔':(2,2,1.3,'GEAR'),
 '战术胸挂':(3,3,1.4,'GEAR'), '工具':(2,1,.65,'TOOLS'), '情报':(1,2,.12,'INTEL'),
 '电钻':(2,2,2.2,'TOOLS'), '饮用水':(1,2,.65,'FOOD')}
def item(name,w=None,h=None,kg=None):
    spec=CATALOG.get(name,(1,1,.3,'SUPPLY'))
    return {'id':next(_ids),'name':name,'w':w or spec[0],'h':h or spec[1],'kg':spec[2] if kg is None else kg,'kind':spec[3]}
def free_position(items,w,h,cols=6,rows=5):
    for y in range(rows-h+1):
        for x in range(cols-w+1):
            if not any(x<i['x']+i['w'] and x+w>i['x'] and y<i['y']+i['h'] and y+h>i['y'] for i in items):return x,y
    return None
def insert(items,entry):
    p=free_position(items,entry['w'],entry['h'])
    if p is None:return False
    entry['x'],entry['y']=p;items.append(entry);return True
def contents(primary=None,corpse=False):
    names=['MK18 风格步枪','FAST 风格头盔','STANAG 弹匣','5.56 弹药','绷带','止痛药'] if corpse else [primary or '工具','绷带','5.56 弹药','饮用水']
    result=[]
    for name in names:
        entry=item(name);entry['known']=False;assert insert(result,entry)
    return result
def transfer(source,destination,entry):
    if entry not in source or not entry.get('known',True):return False
    p=free_position(destination,entry['w'],entry['h'])
    if p is None:return False
    source.remove(entry);entry['x'],entry['y']=p;destination.append(entry);return True

SLOTS=('head','primary1','primary2')
def accepts(slot,entry):
    return entry.get('known',True) and (entry['name']=='FAST 风格头盔' if slot=='head' else slot in SLOTS and entry['kind']=='WEAPON')

def fits(items,entry,x,y):
    return 0<=x<=6-entry['w'] and 0<=y<=5-entry['h'] and not any(i is not entry and x<i['x']+i['w'] and x+entry['w']>i['x'] and y<i['y']+i['h'] and y+entry['h']>i['y'] for i in items)

def move(equipment,source,destination,entry,position=None):
    """A source/destination is a grid list or equipment slot name. Validate first."""
    slot_source=isinstance(source,str);slot_dest=isinstance(destination,str)
    if not entry.get('known',True):return False
    if slot_source:
        if equipment.get(source) is not entry:return False
    elif not any(i is entry for i in source):return False
    if slot_dest:
        if not accepts(destination,entry):return False
        old=equipment.get(destination)
        if old is entry:return True
        if old:
            if slot_source:
                if not accepts(source,old):return False
            else:
                remaining=[i for i in source if i is not entry]
                oldpos=free_position(remaining,old['w'],old['h'])
                if oldpos is None:return False
    else:
        position=position if position is not None else free_position([i for i in destination if i is not entry],entry['w'],entry['h'])
        if position is None or not fits(destination,entry,*position):return False
    if slot_source:equipment[source]=None
    else:source.remove(entry)
    if slot_dest:
        equipment[destination]=entry
        if old:
            if slot_source:equipment[source]=old
            else:old['x'],old['y']=oldpos;source.append(old)
    else:entry['x'],entry['y']=position;destination.append(entry)
    return True
