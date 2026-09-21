import unreal as u,os,json
T=os.path.dirname(__file__);report={}
for folder in ['HK416','EOTechXPS3Scope']:
    paths=u.EditorAssetLibrary.list_assets('/Game/Game/Assets/Models/Weapons/'+folder)
    for path in paths:
        a=u.load_asset(path)
        if not a:report[path]='FAILED';continue
        data={'class':a.get_class().get_name()}
        if isinstance(a,(u.StaticMesh,u.SkeletalMesh)):
            data['bounds']=str(a.get_bounds())
            data['materials']=str(a.get_editor_property('static_materials' if isinstance(a,u.StaticMesh) else 'materials'))
            data['metadata']=str(u.EditorAssetLibrary.get_metadata_tag_values(a))
        report[path]=data
open(os.path.join(T,'hk416_inspect.json'),'w').write(json.dumps(report,indent=2))
task=u.AssetExportTask();task.object=u.load_asset('/Game/Game/Assets/Models/Weapons/EOTechXPS3Scope/EOTechXPS3');task.filename=os.path.join(T,'holo.obj');task.automated=True;task.prompt=False;task.exporter=u.StaticMeshExporterOBJ();u.Exporter.run_asset_export_task(task)
lib=u.get_default_object(u.load_class(None,'/Script/ProceduralMeshComponent.KismetProceduralMeshLibrary'))
values=lib.call_method('GetSectionFromStaticMesh',args=(task.object,0,1))
open(os.path.join(T,'holo_sections.txt'),'w').write(str([str(v) for v in values[0]]))
