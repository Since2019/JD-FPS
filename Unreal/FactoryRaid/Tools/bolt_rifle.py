"""CC0 Poly Haven rifle. Original authored geometry and assembled coordinates."""
import unreal as u,math
NAME='7.62 栓动步枪'
class BoltRifle:
    def __init__(self,s,gun):
        self.s=s;self.parts=[];self.bolts=[];self.mount=u.Vector(-.0498893,25.6486015,9.9083507)
        api=u.get_default_object(u.GameplayStatics)
        for suffix in ['', '_bolt_a','_bolt_b','_scope','_trigger','_wrap']:
            tf=u.Transform();a=api.call_method('BeginDeferredActorSpawnFromClass',args=(s.world,u.StaticMeshActor.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,s.weapon,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));a=api.call_method('FinishSpawningActor',args=(a,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            c=a.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_static_mesh(u.load_asset('/Game/Realism/WeaponTerrain/bolt_action_rifle_7_62/bolt_action_rifle_7_62'+suffix));c.set_cast_shadow(False)
            a.attach_to_component(gun,'',u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.KEEP_WORLD,False);c.set_relative_rotation(u.Rotator(yaw=90),False,True);c.set_relative_location(self.mount,False,True)
            c.set_collision_profile_name('NoCollision');a.set_actor_enable_collision(False);a.set_actor_hidden_in_game(True);self.parts.append(a)
            if suffix=='_scope':self.scope=a
            if suffix in ['_bolt_a','_bolt_b']:self.bolts.append(a)
    def update(self):
        elapsed=self.s.clock-getattr(self.s,'bolt_last_shot',-100)
        slide=5*math.sin(math.pi*(elapsed-.15)/.75) if .15<elapsed<.9 else 0
        for a in self.bolts:a.static_mesh_component.set_relative_location(self.mount+u.Vector(0,-slide,0),False,True)
        for a in self.parts:a.set_actor_enable_collision(False)
