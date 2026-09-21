import unreal as u, os, json
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
level.load_level('/Game/Factory/Maps/ClassicFactoryArmed')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
npc_cls=u.load_class(None,'/Game/Variant_Shooter/Blueprints/AI/BP_ShooterNPC.BP_ShooterNPC_C')
assert npc_cls
controller_bp=u.load_asset('/Game/Variant_Shooter/Blueprints/AI/BP_ShooterAIController')
subsys=u.get_engine_subsystem(u.SubobjectDataSubsystem)
for handle in subsys.k2_gather_subobject_data_for_blueprint(controller_bp):
    data=u.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    obj=u.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data,controller_bp)
    if isinstance(obj,u.StateTreeComponent):
        obj.set_start_logic_automatically(False)
u.BlueprintEditorLibrary.compile_blueprint(controller_bp)
u.get_default_object(u.load_class(None,'/Game/Variant_Shooter/Blueprints/AI/BP_ShooterAIController.BP_ShooterAIController_C')).set_editor_property('start_ai_logic_on_possess',False)
u.EditorAssetLibrary.save_loaded_asset(controller_bp)
def set_any(obj,names,value):
    for name in names:
        try:obj.set_editor_property(name,value);return name
        except Exception:pass
    raise RuntimeError('Missing property '+str(names))
report=[]
for old in actors.get_all_level_actors():
    if old.actor_has_tag('FactoryEnemy'):actors.destroy_actor(old)
spawns=[a.get_actor_location() for a in actors.get_all_level_actors() if a.actor_has_tag('EnemySpawn')]
for index,pos in enumerate(spawns):
    if index==2:pos=u.Vector(-1600,-800,96)
    if index==4:pos=u.Vector(1200,-3000,-244)
    npc=actors.spawn_actor_from_class(npc_cls,pos,u.Rotator(0,135+index*45,0))
    npc.set_actor_label('Factory guard %02d'%(index+1))
    npc.set_editor_property('tags',['FactoryEnemy'])
    npc.set_editor_property('Weapon Class',u.load_class(None,'/Game/Variant_Shooter/Blueprints/Pickups/Weapons/BP_ShooterWeapon_Rifle.BP_ShooterWeapon_Rifle_C'))
    team='NPC blueprint default'
    npc.character_movement.set_editor_property('max_walk_speed',170)
    npc.character_movement.set_editor_property('run_physics_with_no_controller',True)
    report.append({'name':npc.get_name(),'team_property':team,'position':str(pos)})
assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Factory/Maps/ClassicFactoryTactical')
open(os.path.join(os.path.dirname(__file__),'tactical_map_report.json'),'w').write(json.dumps(report,indent=2))
