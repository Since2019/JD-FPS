import unreal as u,os
T=os.path.dirname(__file__)
for name,file in [('Weapon','Weapon.png'),('Helmet','Helmet.jpg')]:
    task=u.AssetImportTask();task.filename=os.path.join(T,'PhotoSource',file);task.destination_path='/Game/Factory/Visual4/UI';task.destination_name='Photo_'+name;task.automated=True;task.replace_existing=True;task.save=True
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);tex=u.load_asset(task.destination_path+'/'+task.destination_name);assert tex
    tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON);tex.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_UI);u.EditorAssetLibrary.save_loaded_asset(tex)
u.log('PHOTO_ICONS_READY')
