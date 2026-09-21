"""Small, bounded UE mesh effects driven by real weapon rounds and projectile stops."""
from runtime_objects import valid
import unreal as u, math, random

class CombatFeedback:
    def __init__(self,session):
        self.s=session;self.world=session.world;self.time=0.;self.pool=[];self.bullets={};self.ammo={};self.impacts=0;self.flashes=0
        self.cls=u.load_class(None,'/Game/Variant_Shooter/Blueprints/Pickups/Projectiles/BP_ShooterProjectile_Bullet.BP_ShooterProjectile_Bullet_C')
        self.cone=u.load_asset('/Engine/BasicShapes/Cone');self.disc=u.load_asset('/Engine/BasicShapes/Cylinder')
        self.materials={n:u.load_asset('/Game/Factory/Effects/'+n) for n in ['M_MuzzleFlash','M_ImpactSpark','M_ImpactMark']}
        assert all(self.materials.values())
        self.random=random.Random(773)

    def spawn(self):
        api=u.get_default_object(u.GameplayStatics)
        transform=u.Transform()
        actor=api.call_method('BeginDeferredActorSpawnFromClass',args=(self.world,u.StaticMeshActor.static_class(),transform,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        actor=api.call_method('FinishSpawningActor',args=(actor,transform,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        actor.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
        actor.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        actor.static_mesh_component.set_cast_shadow(False)
        actor.tags=[u.Name('FactoryTransientFX')]
        entry={'actor':actor,'until':0.,'velocity':u.Vector(),'kind':''};self.pool.append(entry);return entry

    def effect(self,kind,pos,direction,scale,duration,velocity=None):
        entry=next((e for e in self.pool if e['until']<=self.time),None)
        if entry is None:
            if len(self.pool)>=64:entry=min(self.pool,key=lambda e:e['until'])
            else:entry=self.spawn()
        actor=entry['actor'];mesh=actor.static_mesh_component
        mesh.set_static_mesh(self.disc if kind=='M_ImpactMark' else self.cone)
        mesh.set_material(0,self.materials[kind])
        rotation=u.MathLibrary.make_rot_from_z(direction)
        actor.set_actor_location(pos,False,True);actor.set_actor_rotation(rotation,False);actor.set_actor_scale3d(scale)
        actor.set_actor_hidden_in_game(False)
        entry.update(until=self.time+duration,velocity=velocity or u.Vector(),kind=kind)

    def muzzle(self,weapon,player=False):
        self.s.audio.shot(weapon,player)
        wanted='FP_Weapon' if player else 'TP_Weapon'
        mesh=next((m for m in weapon.get_components_by_class(u.SkeletalMeshComponent) if m.get_name()==wanted),None)
        if mesh is None:return
        transform=mesh.get_socket_transform('Muzzle',u.RelativeTransformSpace.RTS_WORLD)
        direction=u.MathLibrary.get_forward_vector(transform.rotation.rotator())
        pos=transform.translation+direction*3
        if player and self.s.weapon_visual.variant=='BOLT':
            tf=mesh.get_world_transform();pos=tf.transform_location(self.s.weapon_visual.bolt.mount+u.Vector(0,59.59,2.5));direction=(tf.transform_location(u.Vector(0,1,0))-tf.translation).normal()
        self.effect('M_MuzzleFlash',pos,direction,u.Vector(.024,.024,.09),.038)
        self.flashes+=1

    def impact(self,bullet):
        pos=bullet.get_actor_location();forward=bullet.get_actor_forward_vector()
        ignored=[bullet]
        instigator=bullet.get_instigator()
        if instigator:ignored.append(instigator)
        hit=self.s.trace(pos-forward*18,pos+forward*25,ignored)
        if not hit:return
        data=u.get_default_object(u.GameplayStatics).call_method('BreakHitResult',args=(hit,))
        actor=data[9];point=data[5];normal=data[6]
        if isinstance(actor,u.Character):return
        self.impacts+=1
        self.s.audio.play('Impact_Metal',point,.23,self.random.uniform(.90,1.10))
        self.effect('M_ImpactMark',point+normal*.12,normal,u.Vector(.025,.025,.0015),18.)
        label=actor.get_actor_label().lower() if actor else ''
        if any(t in label for t in ['steel','tank','pipe','metal','钢','罐','铁']):
            for i in range(3):
                v=normal*self.random.uniform(70,130)+u.Vector(self.random.uniform(-80,80),self.random.uniform(-80,80),self.random.uniform(20,110))
                self.effect('M_ImpactSpark',point+normal*.6,v,u.Vector(.004,.004,.04),self.random.uniform(.10,.19),v)

    def update(self,dt):
        self.time+=dt
        for entry in self.pool:
            if entry['until']<=self.time:entry['actor'].set_actor_hidden_in_game(True)
            elif entry['kind']=='M_ImpactSpark':
                entry['velocity']+=u.Vector(0,0,-400)*dt
                entry['actor'].set_actor_location(entry['actor'].get_actor_location()+entry['velocity']*dt,False,True)
        weapons=[(self.s.weapon,True)]+[(self.s.prop(e['actor'],'Weapon'),False) for e in self.s.enemies if valid(e['actor'])]
        for weapon,is_player in weapons:
            if not weapon or not valid(weapon):continue
            count=self.s.prop(weapon,'Current Bullets')
            if count is not None:
                old=self.ammo.get(weapon,count)
                if count<old:self.muzzle(weapon,is_player)
                self.ammo[weapon]=count
        actors=u.GameplayStatics.get_all_actors_of_class(self.world,self.cls)
        for bullet in actors:
            if bullet in self.bullets:continue
            movement=bullet.get_component_by_class(u.ProjectileMovementComponent)
            if movement and movement.updated_component is None:
                self.impact(bullet);self.bullets[bullet]=True
        self.bullets={b:v for b,v in self.bullets.items() if valid(b)}
