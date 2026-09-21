"""Selected original CC0 assets, exact download URLs and checksums retained."""
import urllib.request,os,json,hashlib,concurrent.futures
T=os.path.dirname(__file__);D=os.path.join(T,'WeaponTerrainSource');os.makedirs(D,exist_ok=True)
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FactoryRaid asset evaluation/1.0'}),timeout=180).read()
manifest=[];jobs=[]
for name in ['bolt_action_rifle_7_62','coastal_cliff_02','snow_field_aerial','snow_02']:
 info=json.loads(get('https://api.polyhaven.com/info/'+name));files=json.loads(get('https://api.polyhaven.com/files/'+name));folder=os.path.join(D,name);os.makedirs(folder,exist_ok=True)
 entry={'id':name,'info':info,'license':'CC0','source':'https://polyhaven.com/a/'+name,'files':{}}
 open(os.path.join(folder,'files.json'),'w').write(json.dumps(files,indent=2))
 selected={}
 if 'fbx' in files:selected['mesh']=files['fbx']['4k']['fbx']
 for channel in files:
  if channel not in ['Diffuse','nor_dx','Rough','Metal','AO','Displacement'] and not (channel.startswith('accesories_') and channel.split('accesories_')[1] in ['diff','nor_dx','rough','metal','ao','alpha']):continue
  choices=files[channel]['4k'];selected[channel]=choices.get('png') if channel=='Displacement' else choices.get('jpg') or choices.get('png')
 for channel,f in selected.items():
  if not f:continue
  path=os.path.join(folder,f['url'].split('/')[-1]);entry['files'][channel]={'path':path,**{k:v for k,v in f.items() if k!='include'}};jobs.append((path,f))
 manifest.append(entry)
def download(job):
 path,f=job
 if not os.path.isfile(path) or hashlib.md5(open(path,'rb').read()).hexdigest()!=f['md5']:
  data=get(f['url']);assert hashlib.md5(data).hexdigest()==f['md5'];open(path,'wb').write(data)
 print(os.path.basename(path),os.path.getsize(path),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(download,jobs))
open(os.path.join(D,'manifest.json'),'w').write(json.dumps(manifest,indent=2))
print('COMPLETE',flush=True)
