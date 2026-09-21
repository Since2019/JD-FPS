import unreal as u
import os, json

level=u.get_editor_subsystem(u.LevelEditorSubsystem)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
level.load_level('/Game/Factory/Maps/ClassicFactory')
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
mode=u.load_class(None,'/Game/Variant_Shooter/Blueprints/BP_ShooterGameMode.BP_ShooterGameMode_C')
assert mode, 'Shooter game mode missing'
world.get_world_settings().set_editor_property('default_game_mode',mode)
table=u.load_asset('/Game/Variant_Shooter/Blueprints/Pickups/DT_WeaponList')
rows=u.DataTableFunctionLibrary.get_data_table_row_names(table)
report={'rows':[str(r) for r in rows], 'table':u.DataTableFunctionLibrary.export_data_table_to_json_string(table)}
pickup_cls=u.load_class(None,'/Game/Variant_Shooter/Blueprints/Pickups/BP_ShooterPickup.BP_ShooterPickup_C')
cdo=u.get_default_object(pickup_cls)
for key in ['Weapon Type','Weapon Class','weapon_type','weapon_class']:
    try:report[key]=str(cdo.get_editor_property(key))
    except Exception as e:report[key]=str(e)
open(os.path.join(os.path.dirname(__file__),'weapon_report.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2))
rifle=next((r for r in rows if 'rifle' in str(r).lower()),None)
assert rifle, 'No rifle row: '+str(rows)
cdo.set_editor_property('Weapon Type',u.DataTableRowHandle(data_table=table,row_name=rifle))
cdo.set_editor_property('Weapon Class',u.load_class(None,'/Game/Variant_Shooter/Blueprints/Pickups/Weapons/BP_ShooterWeapon_Rifle.BP_ShooterWeapon_Rifle_C'))
u.EditorAssetLibrary.save_asset('/Game/Variant_Shooter/Blueprints/Pickups/BP_ShooterPickup')
for old in actors.get_all_level_actors():
    if old.actor_has_tag('FactoryStartingWeapon'):actors.destroy_actor(old)
starts=[a for a in actors.get_all_level_actors() if isinstance(a,u.PlayerStart)]
assert starts, 'No player start'
for start in starts:
    pickup=actors.spawn_actor_from_class(pickup_cls,start.get_actor_location()-u.Vector(0,0,40))
    handle=u.DataTableRowHandle(data_table=table,row_name=rifle)
    pickup.set_editor_property('Weapon Type',handle)
    pickup.set_actor_label('Starting rifle - automatic pickup')
    pickup.set_editor_property('tags',['FactoryStartingWeapon'])
    pickup.rerun_construction_scripts() if hasattr(pickup,'rerun_construction_scripts') else None
assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Factory/Maps/ClassicFactoryArmed')
u.log('FACTORY_ARMED_SAVED')
import runpy
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'finish_starting_weapon.py'),run_name='__main__')
