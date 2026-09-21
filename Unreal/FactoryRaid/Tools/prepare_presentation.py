import unreal as u,os,json
TOOLS=os.path.dirname(__file__)
bp=u.load_asset('/Game/Variant_Shooter/Blueprints/Pickups/BP_ShooterWeaponBase')
u.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,'Firing Montage',True)
u.BlueprintEditorLibrary.compile_blueprint(bp);u.EditorAssetLibrary.save_loaded_asset(bp)
npc_bp=u.load_asset('/Game/Variant_Shooter/Blueprints/AI/BP_ShooterNPC')
u.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(npc_bp,'Weapon Class',True)
u.BlueprintEditorLibrary.compile_blueprint(npc_bp)
npc_default=u.get_default_object(u.load_class(None,'/Game/Variant_Shooter/Blueprints/AI/BP_ShooterNPC.BP_ShooterNPC_C'))
npc_default.set_editor_property('Weapon Class',u.load_class(None,'/Game/Variant_Shooter/Blueprints/Pickups/Weapons/BP_ShooterWeapon_Rifle.BP_ShooterWeapon_Rifle_C'))
u.EditorAssetLibrary.save_loaded_asset(npc_bp)
report={}
for owner,name in [(u.GameplayStatics,'spawn_sound_2d'),(u.GameplayStatics,'spawn_sound_at_location'),(u.AudioMixerLibrary,'start_recording_output'),(u.AudioMixerLibrary,'stop_recording_output')]:
    report[name]=getattr(owner,name).__doc__ if hasattr(owner,name) else 'Missing'
report['sound_methods']={n:getattr(u.GameplayStatics,n).__doc__ for n in dir(u.GameplayStatics) if 'sound' in n.lower()}
sound=u.load_asset('/Game/Weapons/GrenadeLauncher/Audio/FirstPersonTemplateWeaponFire02')
report['shot_sound']=str(sound)
report['shot_duration']=sound.get_editor_property('duration') if sound else None
report['settings']={name:str(getattr(u,name,None)) for name in ['LevelEditorPlaySettings','SoundAttenuationSettings','SoundAttenuation']}
open(os.path.join(TOOLS,'presentation_api.json'),'w').write(json.dumps(report,indent=2))
assets=u.AssetToolsHelpers.get_asset_tools();tasks=[]
shot=u.load_asset('/Game/Factory/Audio/Rifle_Shot')
if not shot:shot=u.EditorAssetLibrary.duplicate_asset('/Game/Weapons/GrenadeLauncher/Audio/FirstPersonTemplateWeaponFire02','/Game/Factory/Audio/Rifle_Shot')
shot.set_editor_property('volume',.45);u.EditorAssetLibrary.save_loaded_asset(shot)
for filename in os.listdir(os.path.join(TOOLS,'PresentationSource')):
    if not filename.endswith(('.obj','.wav')):continue
    name=os.path.splitext(filename)[0];folder='/Game/Factory/PMC' if filename.endswith('.obj') else '/Game/Factory/Audio'
    if filename.endswith('.wav') and u.EditorAssetLibrary.does_asset_exist(folder+'/'+name):continue
    task=u.AssetImportTask();task.filename=os.path.join(TOOLS,'PresentationSource',filename);task.destination_path=folder;task.destination_name=name;task.automated=True;task.save=True
    task.replace_existing=True
    if filename.endswith('.obj'):
        opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False
        opts.static_mesh_import_data.set_editor_property('combine_meshes',True)
        opts.static_mesh_import_data.set_editor_property('auto_generate_collision',False)
        task.options=opts
    tasks.append(task)
assets.import_asset_tasks(tasks)
M=u.MaterialEditingLibrary
for name,tint in [('M_PMC_Uniform',(.10,.13,.065)),('M_PMC_Coyote',(.22,.16,.08)),('M_PMC_Black',(.018,.022,.020)),('M_PMC_Lens',(.018,.03,.036)),('M_PMC_Patch',(.33,.32,.24))]:
    path='/Game/Factory/PMC/'+name;m=u.load_asset(path)
    if True:
        m=m or assets.create_asset(name,'/Game/Factory/PMC',u.Material,u.MaterialFactoryNew())
        M.delete_all_material_expressions(m)
        color=M.create_material_expression(m,u.MaterialExpressionConstant3Vector);color.constant=u.LinearColor(*tint,1)
        if 'Uniform' in name or 'Coyote' in name:
            uv=M.create_material_expression(m,u.MaterialExpressionTextureCoordinate)
            custom=M.create_material_expression(m,u.MaterialExpressionCustom);custom.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
            inputs=[]
            for n in ['UV','Tint']:
                item=u.CustomInput();item.set_editor_property('input_name',n);inputs.append(item)
            custom.set_editor_property('inputs',inputs)
            custom.set_editor_property('code','float2 p=UV*34;float2 a=floor(p);float f=frac(sin(dot(a,float2(12.9898,78.233)))*43758.5453);float weave=0.94+0.06*sin(UV.x*2200)*sin(UV.y*2200);return Tint*lerp(0.64,1.22,smoothstep(0.28,0.72,f))*weave;')
            M.connect_material_expressions(uv,'',custom,'UV');M.connect_material_expressions(color,'',custom,'Tint');M.connect_material_property(custom,'',u.MaterialProperty.MP_BASE_COLOR)
        else:M.connect_material_property(color,'',u.MaterialProperty.MP_BASE_COLOR)
        for value,prop in [(.18 if 'Lens' in name else .94,u.MaterialProperty.MP_ROUGHNESS),(.25 if 'Lens' in name else 0.,u.MaterialProperty.MP_METALLIC)]:
            expr=M.create_material_expression(m,u.MaterialExpressionConstant);expr.r=value;M.connect_material_property(expr,'',prop)
        m.set_editor_property('used_with_skeletal_mesh',True);m.set_editor_property('two_sided',True);M.recompile_material(m)
    u.EditorAssetLibrary.save_loaded_asset(m)
atten=u.load_asset('/Game/Factory/Audio/CombatAttenuation')
if not atten:
    atten=assets.create_asset('CombatAttenuation','/Game/Factory/Audio',u.SoundAttenuation,u.SoundAttenuationFactory())
    settings=atten.get_editor_property('attenuation')
    settings.set_editor_property('attenuate',True);settings.set_editor_property('spatialize',True)
    settings.set_editor_property('attenuation_shape_extents',u.Vector(180,0,0));settings.set_editor_property('falloff_distance',5000.)
    atten.set_editor_property('attenuation',settings);u.EditorAssetLibrary.save_loaded_asset(atten)
