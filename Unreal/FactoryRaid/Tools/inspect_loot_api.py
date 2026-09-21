import unreal as u,json,os
r={}
for name in ['new_object','get_objects_with_outer','find_object','load_object','WidgetBlueprintFactory','UserWidget','CanvasPanel','TextBlock','Border','Button','Image','CanvasPanelSlot','SlateBrush']:
    x=getattr(u,name,None);r[name]=str(x.__doc__)[:2400] if x else None
bp=u.load_asset('/Game/Variant_Shooter/UI/UI_Shooter')
if hasattr(u,'get_objects_with_outer'):r['objects']=[str(x) for x in u.get_objects_with_outer(bp,True)]
try:
    tree=u.find_object(bp,'WidgetTree');r['tree']=str(tree)
    if tree:r['root']=str(tree.get_editor_property('RootWidget'))
except Exception as e:r['tree_error']=str(e)
try:r['tree_objects']=[str(x) for x in u.ObjectIterator() if x.get_outer()==tree]
except Exception as e:r['iterator_error']=str(e)
open(os.path.join(os.path.dirname(__file__),'loot_api.json'),'w').write(json.dumps(r,indent=2))
