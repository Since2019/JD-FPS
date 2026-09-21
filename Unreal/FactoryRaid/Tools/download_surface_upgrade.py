import os,json,urllib.request,hashlib,concurrent.futures
T=os.path.dirname(__file__);D=os.path.join(T,'SurfaceUpgrade');os.makedirs(D,exist_ok=True);manifest=[];jobs=[]
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FactoryRaid asset evaluation/1.0'}),timeout=180).read()
for name in ['blue_metal_plate','concrete_floor_02','concrete_wall_006']:
 files=json.loads(get('https://api.polyhaven.com/files/'+name));info=json.loads(get('https://api.polyhaven.com/info/'+name));entry={'id':name,'info':info,'source':'https://polyhaven.com/a/'+name,'license':'CC0','files':{}}
 for ch in ['Diffuse','nor_dx','Rough','AO']:
  item=files[ch]['4k']['jpg'];path=os.path.join(D,name+'_'+ch+'.jpg');entry['files'][ch]={'path':path,**item};jobs.append((path,item))
 manifest.append(entry)
def run(job):
 path,item=job
 data=get(item['url']);assert hashlib.md5(data).hexdigest()==item['md5'];open(path,'wb').write(data);print(os.path.basename(path),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:list(p.map(run,jobs))
open(os.path.join(D,'manifest.json'),'w').write(json.dumps(manifest,indent=2))
