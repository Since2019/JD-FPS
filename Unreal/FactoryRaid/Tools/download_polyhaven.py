"""Download three selected CC0 assets, retaining provenance and checking hashes."""
import urllib.request,json,os,hashlib,concurrent.futures
ROOT=os.path.join(os.path.dirname(__file__),'PolyHavenSource');os.makedirs(ROOT,exist_ok=True)
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FactoryRaid asset evaluation/1.0'}),timeout=180).read()
manifest=[];jobs=[]
for name in ['portable_generator','metal_tool_chest','old_military_crate']:
    info=json.loads(get('https://api.polyhaven.com/info/'+name));files=json.loads(get('https://api.polyhaven.com/files/'+name))
    folder=os.path.join(ROOT,name);os.makedirs(folder,exist_ok=True)
    open(os.path.join(folder,'info.json'),'w').write(json.dumps(info,indent=2));open(os.path.join(folder,'files.json'),'w').write(json.dumps(files,indent=2))
    selected={'mesh':files['fbx']['4k']['fbx']}
    for channel in ['Diffuse','nor_dx','Rough','Metal','AO','Alpha']:
        if channel in files:
            options=files[channel]['4k'];selected[channel]=options.get('png') or options.get('jpg') or options['exr']
    entry={'id':name,'source':'https://polyhaven.com/a/'+name,'license':'CC0','license_url':'https://polyhaven.com/license','info':info,'files':{}}
    for channel,item in selected.items():
        path=os.path.join(folder,item['url'].split('/')[-1]);entry['files'][channel]={'path':path,**{k:v for k,v in item.items() if k!='include'}};jobs.append((path,item))
    manifest.append(entry)
def download(job):
    path,item=job
    if not os.path.isfile(path) or hashlib.md5(open(path,'rb').read()).hexdigest()!=item['md5']:
        data=get(item['url']);assert hashlib.md5(data).hexdigest()==item['md5'],path
        open(path,'wb').write(data)
    print(os.path.basename(path),os.path.getsize(path),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(download,jobs))
open(os.path.join(ROOT,'manifest.json'),'w').write(json.dumps(manifest,indent=2))
print('COMPLETE',len(jobs),flush=True)
