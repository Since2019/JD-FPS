"""Original modular PMC dress mounted to animated skeletons."""
from runtime_objects import valid
import unreal as u
class PMCAppearance:
    def __init__(self,session):self.s=session;self.applied={};self.parts=[]
    def part(self,npc,mesh,bone,name,offset,material,scale=None):
        asset=u.load_asset('/Game/Factory/Visual4/Meshes/'+name) if name.startswith('FAST_') else u.load_asset('/Game/Factory/Visual3/Meshes/PMC_ClothUV') if name=='PMC_FabricLimb' else u.load_asset('/Game/Factory/Visual2/PMC/'+name) if u.EditorAssetLibrary.does_asset_exist('/Game/Factory/Visual2/PMC/'+name) else u.load_asset('/Game/Factory/PMC/'+name)
        assert asset,'Missing PMC mesh '+name
        api=u.get_default_object(u.GameplayStatics);tf=u.Transform()
        actor=api.call_method('BeginDeferredActorSpawnFromClass',args=(self.s.world,u.StaticMeshActor.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,npc,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        actor=api.call_method('FinishSpawningActor',args=(actor,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        c=actor.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_static_mesh(asset);c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        path='/Game/Factory/Visual4/Materials/'+material
        if not u.EditorAssetLibrary.does_asset_exist(path):path='/Game/Factory/Visual3/Materials/'+material
        selected=u.load_asset(path) if u.EditorAssetLibrary.does_asset_exist(path) else u.load_asset('/Game/Factory/Visual2/PMC/'+material) if u.EditorAssetLibrary.does_asset_exist('/Game/Factory/Visual2/PMC/'+material) else u.load_asset('/Game/Factory/PMC/'+material)
        for slot in range(max(1,c.get_num_materials())):c.set_material(slot,selected)
        rot=npc.get_actor_rotation();f=u.MathLibrary.get_forward_vector(rot);r=u.MathLibrary.get_right_vector(rot)
        pos=mesh.get_socket_location(bone)+f*offset[0]+r*offset[1]+u.Vector(0,0,offset[2])
        actor.set_actor_location(pos,False,True);actor.set_actor_rotation(rot,False)
        if scale:actor.set_actor_scale3d(u.Vector(*scale))
        actor.attach_to_component(mesh,bone,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
        actor.tags=[u.Name('FactoryPMCGear')];self.parts.append((npc,actor))
        return actor
    def limb(self,npc,mesh,start,end,radius,material):
        actor=self.part(npc,mesh,start,'PMC_FabricLimb',(0,0,0),material)
        a=mesh.get_socket_location(start);b=mesh.get_socket_location(end);d=b-a
        length=(d.x*d.x+d.y*d.y+d.z*d.z)**.5
        actor.detach_from_actor(u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD,u.DetachmentRule.KEEP_WORLD)
        actor.set_actor_location((a+b)*.5,False,True)
        actor.set_actor_rotation(u.MathLibrary.make_rot_from_z(d),False)
        actor.set_actor_scale3d(u.Vector(radius,radius,length*.96))
        actor.attach_to_component(mesh,start,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
    def dress(self,npc,index):
        mesh=npc.mesh
        weapon=self.s.prop(npc,'Weapon')
        if weapon and not weapon.actor_has_tag('FactoryMK18'):
            material=u.load_asset('/Game/Factory/Effects/M_TacticalRifle')
            for part in weapon.get_components_by_class(u.SkeletalMeshComponent):part.set_material(0,material)
        uniform=u.load_asset('/Game/Factory/Visual4/Materials/M_PMC_Uniform');black=u.load_asset('/Game/Factory/Visual4/Materials/M_PMC_Black')
        for i in range(mesh.get_num_materials()):mesh.set_material(i,uniform if i==0 else black)
        cloth='M_PMC_Coyote' if index%2==0 else 'M_PMC_Uniform'
        specs=[
          ('spine_03','PMC_Vest',(1,0,14),cloth,None),
          ('spine_03','PMC_MagPouches',(15,0,6),cloth,None),
          ('spine_03','PMC_Webbing',(14,0,13),'M_PMC_Black',None),
          ('spine_03','PMC_Backpack',(-19,0,15),cloth,None),
          ('pelvis','PMC_Belt',(0,0,5),'M_PMC_Black',None),
          ('head','PMC_Balaclava',(3,0,8),'M_PMC_Black',(1.2,1,1)),
          ('head','FAST_Shell',(3,0,15),'M_PMC_Helmet',None),
          ('head','FAST_Hardware',(3,0,15),'M_FAST_Hardware',None),
          ('head','FAST_Loop',(3,0,15),'M_FAST_Loop',None),
          ('head','FAST_Straps',(3,0,15),'M_FAST_Straps',None),
          ('head','PMC_GoggleFrame',(16,0,13),'M_PMC_Black',None),
          ('head','PMC_GoggleLens',(17.2,0,13),'M_PMC_Lens',None),
          ('calf_l','PMC_Kneepad',(6,0,0),'M_PMC_Black',None),
          ('calf_r','PMC_Kneepad',(6,0,0),'M_PMC_Black',None),
          ('spine_03','PMC_Patch',(14.5,0,26),'M_PMC_Patch',None),
          ('spine_03','PMC_Seams',(1,0,14),'M_PMC_Coyote',None),
          ('spine_03','PMC_Buckles',(1,0,14),'M_PMC_Black',None),
          ('spine_03','PMC_Radio',(10,-18,19),'M_PMC_Black',None),
          ('pelvis','PMC_UtilityPouch',(0,20,2),cloth,None),
          ('pelvis','PMC_UtilityPouch',(-6,-19,2),cloth,(.8,.8,.8)),
          ('spine_03','PMC_Zipper',(-28,0,15),'M_PMC_Black',None)]
        for bone,name,offset,mat,scale in specs:self.part(npc,mesh,bone,name,offset,mat,scale)
        for side in ['l','r']:
            self.limb(npc,mesh,'upperarm_'+side,'lowerarm_'+side,6.1,'M_PMC_Uniform')
            self.limb(npc,mesh,'lowerarm_'+side,'hand_'+side,4.9,'M_PMC_Uniform')
            self.limb(npc,mesh,'thigh_'+side,'calf_'+side,8.4,'M_PMC_Uniform')
            self.limb(npc,mesh,'calf_'+side,'foot_'+side,6.3,'M_PMC_Uniform')
            self.part(npc,mesh,'foot_'+side,'PMC_Boot',(6,0,-4),'M_PMC_Black')
            self.part(npc,mesh,'hand_'+side,'PMC_FabricLimb',(4,0,0),'M_PMC_Black',(4.8,4.3,10))
        npc.tags=list(npc.tags)+[u.Name('FactoryPMC')];self.applied[npc]=True
    def update(self):
        if self.s.clock<.6:return
        for i,entry in enumerate(self.s.enemies):
            npc=entry['actor']
            if valid(npc) and npc not in self.applied:self.dress(npc,i)
        for npc,actor in self.parts:
            if not valid(npc) and valid(actor):actor.destroy_actor()
