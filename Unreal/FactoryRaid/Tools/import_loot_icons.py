import unreal as u,os
T=os.path.dirname(__file__);A=u.AssetToolsHelpers.get_asset_tools()
for name in ['Weapon','Helmet']:
    task=u.AssetImportTask();task.filename=os.path.join(T,'Visual4Source','Icon_'+name+'.png');task.destination_path='/Game/Factory/Visual4/UI';task.destination_name='Icon_'+name;task.automated=True;task.save=True;task.replace_existing=True;A.import_asset_tasks([task])
    tex=u.load_asset('/Game/Factory/Visual4/UI/Icon_'+name);tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON);tex.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_UI);assert u.EditorAssetLibrary.save_loaded_asset(tex)
u.log('LOOT_ICONS_IMPORTED')
