"""Replace template weapon render geometry, retaining the functioning rig and weapon BP."""
from runtime_objects import valid
import unreal as u
class WeaponAppearance:
    def __init__(self,session):
        self.s=session;self.applied={};self.parts=[];self.player_parts=[]
        self.materials={name:u.load_asset('/Game/Factory/Visual4/Materials/'+name) or u.load_asset('/Game/Factory/Visual3/Materials/'+name) for name in ['M_Receiver','M_RIS','M_Hardware','M_Polymer','M_Dark','M_HiddenTemplate']}
        self.apply(session.weapon,True)
        self.mk18_parts=list(self.player_parts);self.hk_parts=[];self.variant='MK18'
        api=u.get_default_object(u.GameplayStatics);tf=u.Transform()
        a=api.call_method('BeginDeferredActorSpawnFromClass',args=(session.world,u.SkeletalMeshActor.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,session.weapon,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        a=api.call_method('FinishSpawningActor',args=(a,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        c=a.skeletal_mesh_component;c.set_skeletal_mesh_asset(u.load_asset('/Game/Game/Assets/Models/Weapons/HK416/HK416'));c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);c.set_cast_shadow(False)
        c.set_material(1,self.materials['M_HiddenTemplate'])
        gun=next(c for c in session.weapon.get_components_by_class(u.SkeletalMeshComponent) if c.get_name()=='FP_Weapon')
        a.attach_to_component(gun,'',u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.KEEP_WORLD,False)
        c.set_relative_rotation(u.Rotator(yaw=-90),False,True);c.set_relative_location(u.Vector(0,13,-7),False,True)
        a.set_actor_hidden_in_game(True);self.hk_parts=[a];self.player_parts.append(a);self.parts.append((session.weapon,a))
    def select(self,entry):
        self.variant='HK416' if entry and entry['name']=='HK416' else 'MK18'
        for a in self.mk18_parts:a.set_actor_hidden_in_game(not entry or self.variant!='MK18')
        for a in self.hk_parts:a.set_actor_hidden_in_game(not entry or self.variant!='HK416')
    def apply(self,weapon,player=False):
        if not weapon or weapon in self.applied:return
        mesh=next((c for c in weapon.get_components_by_class(u.SkeletalMeshComponent) if c.get_name()==('FP_Weapon' if player else 'TP_Weapon')),None)
        if not mesh:return
        for c in weapon.get_components_by_class(u.SkeletalMeshComponent):
            for i in range(c.get_num_materials()):c.set_material(i,self.materials['M_HiddenTemplate'])
            c.set_cast_shadow(False)
        api=u.get_default_object(u.GameplayStatics)
        for name,material in [('MK18_Receiver','M_Receiver'),('MK18_RIS','M_RIS'),('MK18_Hardware','M_Hardware'),('MK18_Polymer','M_Polymer'),('MK18_Dark','M_Dark')]:
            tf=u.Transform();a=api.call_method('BeginDeferredActorSpawnFromClass',args=(self.s.world,u.StaticMeshActor.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,weapon,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            a=api.call_method('FinishSpawningActor',args=(a,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            c=a.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_static_mesh(u.load_asset('/Game/Factory/Visual3/Meshes/'+name))
            for slot in range(max(1,c.get_num_materials())):c.set_material(slot,self.materials[material])
            c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);c.set_cast_shadow(not player)
            a.attach_to_component(mesh,'',u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.KEEP_WORLD,False)
            a.tags=[u.Name('FactoryMK18Visual')];self.parts.append((weapon,a))
            if player:self.player_parts.append(a)
        weapon.tags=list(weapon.tags)+[u.Name('FactoryMK18')];self.applied[weapon]=True
    def update(self):
        for e in self.s.enemies:
            if valid(e['actor']):self.apply(self.s.prop(e['actor'],'Weapon'))
        for w,a in self.parts:
            if not valid(w) and valid(a):a.destroy_actor()
