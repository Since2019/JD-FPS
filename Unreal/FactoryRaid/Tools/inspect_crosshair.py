import unreal as u,os,json
R={};T=os.path.dirname(__file__)
for path in ['/Game/Variant_Shooter/UI/UI_Shooter','/Game/Variant_Shooter/Blueprints/BP_ShooterPlayerController']:
    a=u.load_asset(path);r={}
    for name in ['widget_tree','WidgetTree']:
        try:
            tree=a.get_editor_property(name);r[name]=str(tree)
            root=tree.get_editor_property('root_widget');r['root']=str(root)
            pending=[root];r['widgets']=[]
            while pending:
                item=pending.pop();r['widgets'].append({'name':item.get_name(),'class':item.get_class().get_name()})
                try:pending.extend(item.call_method('GetAllChildren'))
                except Exception:pass
        except Exception as e:r[name]=str(e)
    R[path]=r
open(os.path.join(T,'crosshair_inspect.json'),'w').write(json.dumps(R,indent=2))
