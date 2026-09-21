"""Editor-PIE gameplay extension. Uses UE collision, characters and weapon blueprints.

This is deliberately kept separate from the uncompiled native game module. It is
not a shipping-runtime Python plugin and must be started by play_tactical.py.
"""
import unreal as u
import math, random

def length(v):return math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z)
def dot(a,b):return a.x*b.x+a.y*b.y+a.z*b.z
def unit(v):return v/max(length(v),.0001)
def lerp(a,b,t):return a+(b-a)*min(1,max(0,t))
from runtime_objects import valid
def prop(obj,name,default=None):
    try:return obj.get_editor_property(name)
    except Exception:return default
def vec_copy(v):return u.Vector(v.x,v.y,v.z)
def rotate(v,r):return u.MathLibrary.get_forward_vector(r)*v.x+u.MathLibrary.get_right_vector(r)*v.y+u.MathLibrary.get_up_vector(r)*v.z
def smooth_factor(rate,dt):return 1.-math.exp(-rate*dt)
def damp_spring(value,velocity,omega,dt):
    c=velocity+omega*value;e=math.exp(-omega*dt)
    return (value+c*dt)*e,(velocity-omega*c*dt)*e
def input_key(name):
    key=u.Key();key.set_editor_property('key_name',name);return key

class TacticalSession:
    prop=staticmethod(prop)
    def __init__(self,world,player,test=False):
        self.world=world;self.player=player;self.pc=player.get_controller();self.test=test
        self.is_icebreaker='Icebreaker' in world.get_name()
        self.clock=0.;self.lean=0.;self.ads=0.;self.previous=set();self.pack=[];self.inventory=False
        self.recoil=0.;self.recoil_velocity=0.;self.kick=0.;self.kick_velocity=0.;self.rounds_seen=None
        self.sprint_alpha=0.;self.sprinting=False;self.run_phase=0.;self.trigger_active=False
        self.search=None;self.search_time=0.;self.search_origin=None;self.focus=None
        self.message='';self.message_until=0.;self.hud_time=0.;self.ai_time=0.;self.kills=0
        self.ai_enabled=True;self.ai_damage_enabled=True;self.shots_fired=0
        self.input_keys={name:input_key(name) for name in ['R','C','Z','X','One','Two','Q','E','RightMouseButton','F','Tab','Escape','LeftShift','LeftMouseButton','W','A','S','D']}
        self.camera=next(c for c in player.get_components_by_class(u.CameraComponent) if 'FirstPerson' in c.get_name())
        self.camera_origin=vec_copy(self.camera.get_editor_property('relative_location'))
        self.eye_height=64.
        self.camera.use_pawn_control_rotation=False
        self.camera.attach_to_component(player.root_component,'',u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
        self.camera.set_absolute(False,True,False)
        # The template camera carries a 0.3 component scale; optical centimetres need 1:1.
        self.camera.set_world_scale3d(u.Vector(1,1,1))
        self.camera.set_enable_first_person_scale(False)
        u.SystemLibrary.execute_console_command(world,'r.SetNearClipPlane 1')
        self.fp_mesh=next((c for c in player.get_components_by_class(u.SkeletalMeshComponent) if 'FirstPerson' in c.get_name()),None)
        self.fp_origin=self.fp_mesh.get_relative_transform() if self.fp_mesh else None
        self.aim_rear=u.Vector(0,0,18.5)
        self.aim_front=u.Vector(0,15,18.5)
        self.pose_calibrated=False
        self.eye_relief=9.
        self.aim_error=0.
        self.anim=None
        for mesh in player.get_components_by_class(u.SkeletalMeshComponent):
            inst=mesh.get_anim_instance()
            if inst and prop(inst,'Is Aiming') is not None:self.anim=inst;break
        self.anim_has_ads=False
        if self.anim:
            try:self.anim.set_editor_property('Is Aiming',False);self.anim_has_ads=True
            except Exception:pass
        self.player.character_movement.max_walk_speed=290
        self.player.character_movement.max_acceleration=950
        self.player.character_movement.braking_deceleration_walking=750
        self.weapon=prop(player,'Current Weapon')
        if not self.weapon:
            rifle=u.load_class(None,'/Game/Variant_Shooter/Blueprints/Pickups/Weapons/BP_ShooterWeapon_Rifle.BP_ShooterWeapon_Rifle_C')
            player.call_method('Add Weapon Class',args=(rifle,))
            self.weapon=prop(player,'Current Weapon')
        rifle_material=u.load_asset('/Game/Factory/Effects/M_TacticalRifle')
        if rifle_material and valid(self.weapon):
            for mesh in self.weapon.get_components_by_class(u.SkeletalMeshComponent):mesh.set_material(0,rifle_material)
        if valid(self.weapon):
            self.weapon.set_editor_property('Firing Recoil',0.)
            self.weapon.set_editor_property('Firing Montage',None)
        # Equipping the rifle replaces the copy-pose anim instance with its weapon rig.
        if self.fp_mesh:
            # Retain M_Mannequin's head/body cutout; only adjust exposed finish.
            self.fp_finishes=[]
            for slot in range(self.fp_mesh.get_num_materials()):
                finish=self.fp_mesh.create_dynamic_material_instance(slot)
                finish.set_vector_parameter_value('Paint Tint',u.LinearColor(.12,.15,.09,1) if slot==0 else u.LinearColor(.028,.034,.025,1))
                finish.set_scalar_parameter_value('MetalPaintMetallic',0.)
                finish.set_scalar_parameter_value('MetalPaintRoughness',.82)
                finish.set_scalar_parameter_value('EmissivePower',0.)
                self.fp_finishes.append(finish)
            aiming_class=u.load_class(None,'/Game/Factory/Animation/ABP_TacticalWeapon.ABP_TacticalWeapon_C')
            if aiming_class:self.fp_mesh.set_anim_instance_class(aiming_class)
            self.anim=self.fp_mesh.get_anim_instance()
            if prop(self.anim,'Is Aiming') is not None:
                self.anim.set_editor_property('Is Aiming',False)
                self.anim_has_ads=True
        all_actors=u.GameplayStatics.get_all_actors_of_class(world,u.Actor)
        self.boxes=[];self.enemies=[];self.box_lids=[]
        for actor in all_actors:
            if actor.actor_has_tag('Loot'):
                tags=[str(t) for t in actor.tags]
                self.boxes.append({'actor':actor,'item':tags[2] if len(tags)>2 else '物资','searched':False,'title':actor.get_actor_label().replace('Loot | ','')})
            if actor.actor_has_tag('FactoryEnemy') or actor.get_class().get_name()=='BP_ShooterNPC_C':
                controller=actor.get_controller()
                if controller:
                    brain=prop(controller,'brain_component')
                    if brain:brain.stop_logic('Factory tactical local controller')
                    controller.stop_movement() if hasattr(controller,'stop_movement') else None
                self.enemies.append({'actor':actor,'home':vec_copy(actor.get_actor_location()),'last':None,'alert':0.,'next_fire':3.+len(self.enemies)*.3,'dead':False,'side':1,'seen':0.,'burst':0,'move':u.Vector(),'hp':prop(actor,'Current HP',100.)})
            if isinstance(actor,u.StaticMeshActor) and '箱盖' in actor.get_actor_label():self.box_lids.append(actor)
        self.add_item('医疗包',2,1,.6)
        from combat_feedback import CombatFeedback
        self.feedback=CombatFeedback(self)
        from combat_audio import CombatAudio
        from pmc_appearance import PMCAppearance
        self.audio=CombatAudio(self);self.pmc=PMCAppearance(self)
        from weapon_appearance import WeaponAppearance
        self.weapon_visual=WeaponAppearance(self)
        # A dedicated context gives this controller ownership of the trigger, so native
        # Enhanced Input cannot fire a first shot while the sprint pose is lowering.
        subsystem_api=u.get_default_object(u.load_class(None,'/Script/Engine.SubsystemBlueprintLibrary'))
        self.input_subsystem=subsystem_api.call_method('GetLocalPlayerSubSystem',args=(self.pc,u.EnhancedInputLocalPlayerSubsystem.static_class()))
        original=u.load_asset('/Game/Variant_Shooter/Input/IMC_Weapons')
        self.trigger_context=u.load_asset('/Game/Factory/Visual3/Input/IMC_TacticalWeapons')
        assert self.trigger_context,'Missing tactical input context'
        self.input_subsystem.remove_mapping_context(original)
        self.input_subsystem.add_mapping_context(self.trigger_context,1)
        from scope_optic import ScopeOptic
        self.optic=ScopeOptic(self)
        from loot_runtime import LootInterface
        self.loot=LootInterface(self)
        from stance_runtime import Stance
        self.stance=Stance(self)
        self.say('Shift 冲刺 · Q/E 侧倾 · 右键瞄准 · F 打开箱子/尸体 · Tab 背包',8)

    def say(self,text,seconds=2):self.message=text;self.message_until=self.clock+seconds
    def ignored(self):return [a for a in [self.player,prop(self.player,'Current Weapon')] if valid(a)]
    def trace(self,start,end,ignore=None,radius=0):
        args=(self.world,start,end)
        if radius:
            return u.SystemLibrary.sphere_trace_single(*args,radius,u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignore or self.ignored(),u.DrawDebugTrace.NONE)
        return u.SystemLibrary.line_trace_single(*args,u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,ignore or self.ignored(),u.DrawDebugTrace.NONE)
    def hit_actor(self,hit):return u.get_default_object(u.GameplayStatics).call_method('BreakHitResult',args=(hit,))[9] if hit else None
    def hit_point(self,hit):return u.get_default_object(u.GameplayStatics).call_method('BreakHitResult',args=(hit,))[5] if hit else None
    def keys(self):
        return {name for name,key in self.input_keys.items() if self.pc.is_input_key_down(key) or (name in {'One','Two','X','C','Z','F','Tab','Escape'} and self.pc.was_input_key_just_pressed(key))}

    def update_camera(self,dt,keys):
        speed=length(self.player.get_velocity())
        moving=bool(keys & {'W','A','S','D'}) or speed>20
        self.sprinting=self.stance.mode=='stand' and 'LeftShift' in keys and moving and not self.inventory and self.search is None
        self.sprint_alpha=lerp(self.sprint_alpha,1. if self.sprinting else 0.,smooth_factor(8.,dt))
        self.run_phase+=dt*(1.2+min(speed,480)/480*.25)*math.tau
        want_aim=self.loot.equipment.loaded is not None and self.clock>=self.loot.equipment.ready_at and 'RightMouseButton' in keys and not self.sprinting and not self.inventory and self.search is None
        self.ads=lerp(self.ads,1. if want_aim else 0.,smooth_factor(10.,dt))
        weapon=prop(self.player,'Current Weapon')
        rounds=prop(weapon,'Current Bullets')
        if rounds is not None and self.rounds_seen is not None and rounds<self.rounds_seen:
            shots=min(4,self.rounds_seen-rounds)
            self.recoil_velocity+=shots*lerp(7.,4.5,self.ads)
            self.kick_velocity+=shots*lerp(36.,23.,self.ads)
        self.rounds_seen=rounds
        old_recoil=self.recoil
        self.recoil,self.recoil_velocity=damp_spring(self.recoil,self.recoil_velocity,13.,dt)
        self.kick,self.kick_velocity=damp_spring(self.kick,self.kick_velocity,22.,dt)
        control=self.pc.get_control_rotation()
        self.pc.set_control_rotation(u.Rotator(pitch=control.pitch+self.recoil-old_recoil,yaw=control.yaw,roll=control.roll))
        target=(int('E' in keys)-int('Q' in keys))*22. if not self.inventory else 0.
        root=self.player.get_actor_location();view=self.pc.get_control_rotation()
        right=u.MathLibrary.get_right_vector(u.Rotator(yaw=view.yaw))
        base=root+u.Vector(0,0,self.eye_height)
        obstruction=self.trace(base,base+right*target,radius=9) if abs(target)>.1 else None
        if obstruction:target=0.
        self.lean=lerp(self.lean,target,smooth_factor(12.,dt))
        self.camera.set_world_location(base+right*self.lean,False,True)
        # UE positive roll leans the eye right. The old minus sign inverted the visual lean.
        camera_rot=u.Rotator(pitch=view.pitch,yaw=view.yaw,roll=self.lean*.40)
        self.camera.set_world_rotation(camera_rot,False,True)
        self.camera.set_field_of_view(90.)
        # One continuous pose solver owns ADS; avoid the template's binary pose switch.
        if self.anim_has_ads:self.anim.set_editor_property('Is Aiming',False)
        # The template uses a separate first-person projection for hands and weapon.
        self.camera.set_first_person_field_of_view(90.)
        self.update_weapon_pose(camera_rot)
        weapon=prop(self.player,'Current Weapon')
        if valid(weapon):
            weapon.set_editor_property('Aim Variance',lerp(20.,0.,self.ads))
            weapon.set_editor_property('Firing Recoil',0.)
        self.player.character_movement.max_walk_speed=65 if self.stance.mode=='prone' else 125 if self.stance.mode=='crouch' else 480 if self.sprinting else 175 if want_aim else 290

    def update_trigger(self,keys):
        blocked=self.loot.equipment.loaded is None or self.clock<self.loot.equipment.ready_at or self.sprinting or self.sprint_alpha>.18 or self.inventory or self.search is not None
        held='LeftMouseButton' in keys and not blocked
        if self.weapon_visual.variant=='BOLT':
            entry=self.loot.equipment.loaded
            if entry is None:self.weapon.call_method('Stop Firing');self.trigger_active=False;return
            entry.setdefault('bolt_ammo',max(0,min(5,prop(self.weapon,'Current Bullets',0))))
            self.weapon.set_editor_property('Current Bullets',entry['bolt_ammo'])
            if getattr(self,'bolt_reload_until',0):
                if self.clock>=self.bolt_reload_until:entry['bolt_ammo']=5;self.weapon.set_editor_property('Current Bullets',5);self.bolt_reload_until=0
                else:held=False
            if 'R' in keys and 'R' not in self.previous and not blocked and not getattr(self,'bolt_reload_until',0) and prop(self.weapon,'Current Bullets',0)<5:
                self.bolt_reload_until=self.clock+2.8;held=False;self.say('装填 7.62 弹药…')
            if held and 'LeftMouseButton' not in self.previous and self.clock>=getattr(self,'bolt_next_shot',0) and prop(self.weapon,'Current Bullets',0)>0:
                # Keep the template's internal shot above zero so its automatic
                # refill branch never executes; this item's counter is authoritative.
                self.weapon.set_editor_property('Current Bullets',max(2,entry['bolt_ammo']))
                self.weapon.call_method('Start Firing');self.weapon.call_method('Stop Firing');entry['bolt_ammo']-=1;entry['ammo']=entry['bolt_ammo'];self.weapon.set_editor_property('Current Bullets',entry['bolt_ammo']);self.bolt_last_shot=self.clock;self.bolt_next_shot=self.clock+1.2
            else:self.weapon.call_method('Stop Firing')
            self.trigger_active=False
            return
        if held and not self.trigger_active:self.weapon.call_method('Start Firing')
        elif (not held and self.trigger_active) or blocked:self.weapon.call_method('Stop Firing')
        self.trigger_active=held

    def update_weapon_pose(self,view):
        if not self.fp_mesh:return
        weapon=prop(self.player,'Current Weapon')
        if not valid(weapon):return
        gun=next((m for m in weapon.get_components_by_class(u.SkeletalMeshComponent) if m.get_name()=='FP_Weapon'),None)
        if not gun:return
        if not self.pose_calibrated:
            if self.clock<.25:return
            # Capture the evaluated rifle grip once. Locomotion/IK must never fight ADS.
            self.fp_mesh.pause_anims=True
            self.fp_mesh.set_component_tick_enabled(False)
            cam=self.camera.get_world_transform();arm=self.fp_mesh.get_world_transform()
            rear_local=arm.inverse_transform_location(gun.get_world_transform().transform_location(self.aim_rear))
            gun_relative=u.MathLibrary.compose_rotators(gun.get_world_rotation(),u.MathLibrary.negate_rotator(self.fp_mesh.get_world_rotation()))
            self.aim_pose_rotation=u.MathLibrary.compose_rotators(u.MathLibrary.negate_rotator(gun_relative),u.Rotator(yaw=-90))
            self.aim_pose_location=u.Vector(self.eye_relief,0,0)-rotate(rear_local,self.aim_pose_rotation)
            self.hip_pose_location=cam.inverse_transform_location(self.fp_mesh.get_world_location())
            if self.is_icebreaker:self.hip_pose_location+=u.Vector(8,3,-9)
            self.hip_pose_rotation=u.MathLibrary.compose_rotators(self.fp_mesh.get_world_rotation(),u.MathLibrary.negate_rotator(self.camera.get_world_rotation()))
            self.fp_mesh.attach_to_component(self.camera,'',u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
            self.pose_calibrated=True
        # Camera-local assembly: no world-space reset or animated socket feedback loop.
        sway=(1-self.ads)*.12*math.sin(self.clock*2.)
        aim_location=self.aim_pose_location+u.Vector(12 if self.weapon_visual.variant=='HK416' else 0,0,0)
        location=self.hip_pose_location+(aim_location-self.hip_pose_location)*self.ads-u.Vector(self.kick,0,0)+u.Vector(0,0,sway)
        rotation=u.MathLibrary.r_lerp(self.hip_pose_rotation,self.aim_pose_rotation,self.ads,True)
        # Low-port sprint cycle pivots around the hands, never the skeleton's feet.
        lower=u.Rotator(pitch=-26,yaw=14,roll=-10);pivot=u.Vector(12,5,-18)
        run_location=pivot+rotate(self.hip_pose_location-pivot,lower)+u.Vector(-3,5,-7)
        run_rotation=u.MathLibrary.compose_rotators(self.hip_pose_rotation,lower)
        bob=u.Vector(.25*math.sin(self.run_phase),.35*math.cos(self.run_phase),.55*math.sin(self.run_phase*2))
        lower_alpha=max(self.sprint_alpha,self.stance.switch_alpha)
        location=location+(run_location-location)*lower_alpha+bob*self.sprint_alpha
        rotation=u.MathLibrary.r_lerp(rotation,run_rotation,lower_alpha,True)
        self.fp_mesh.set_relative_location(location,False,True)
        self.fp_mesh.set_relative_rotation(rotation,False,True)
        final_rear=gun.get_world_transform().transform_location(self.aim_rear)
        final_front=gun.get_world_transform().transform_location(self.aim_front)
        sight_direction=unit(final_front-final_rear)
        self.aim_error=length((final_rear-self.camera.get_world_location())-self.camera.get_forward_vector()*dot(final_rear-self.camera.get_world_location(),self.camera.get_forward_vector()))
        self.sight_alignment=dot(sight_direction,self.camera.get_forward_vector())

    def target_box(self):
        eye=self.camera.get_world_location();forward=self.camera.get_forward_vector();best=None;distance=210.
        for box in self.boxes:
            if box['searched'] or not valid(box['actor']):continue
            pos=box['actor'].get_actor_location();delta=pos-eye;d=length(delta)
            if d>=distance or dot(unit(delta),forward)<.86:continue
            hit=self.trace(eye,pos)
            # Containers themselves block traces. Only accept their immediate surface.
            if hit and length(self.hit_point(hit)-pos)>65:continue
            best=box;distance=d
        return best

    def add_item(self,name,w=1,h=1,kg=.3):
        for y in range(6-h):
            for x in range(7-w):
                if any(x<i['x']+i['w'] and x+w>i['x'] and y<i['y']+i['h'] and y+h>i['y'] for i in self.pack):continue
                self.pack.append({'name':name,'x':x,'y':y,'w':w,'h':h,'kg':kg});return True
        return False

    def update_search(self,dt,keys):
        self.focus=self.target_box()
        if self.inventory or 'F' not in keys or self.focus is None:
            self.search=None;self.search_time=0;return
        if self.search is not self.focus:
            self.search=self.focus;self.search_time=0;self.search_origin=vec_copy(self.player.get_actor_location())
        if length(self.player.get_actor_location()-self.search_origin)>25:
            self.search=None;self.search_time=0;self.say('移动已中断搜索');return
        self.search_time+=dt
        if self.search_time<2.:return
        box=self.search;item=box['item'];w,h,kg=(2,2,2.2) if item=='电钻' else (2,1,.6) if item=='医疗包' else (1,1,.3)
        if self.add_item(item,w,h,kg):
            box['searched']=True;self.say('获得：'+item,4)
            box['actor'].tags=list(box['actor'].tags)+[u.Name('Searched')]
            for lid in self.box_lids:
                if length(lid.get_actor_location()-box['actor'].get_actor_location())<85:
                    lid.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE)
                    lid.set_actor_rotation(u.Rotator(-70,0,0),False)
                    break
        else:self.say('背包已满，箱内物资保留',3)
        self.search=None;self.search_time=0

    def update_ai(self,dt):
        if not self.ai_enabled:return
        player_pos=self.player.get_actor_location();player_eye=self.camera.get_world_location()
        for index,entry in enumerate(self.enemies):
            if entry['dead']:continue
            npc=entry['actor']
            if not valid(npc) or npc.actor_has_tag('Dead') or prop(npc,'Current HP',1)<=0:
                if not entry['dead']:entry['dead']=True;self.kills+=1
                continue
            pos=npc.get_actor_location();eye=pos+u.Vector(0,0,60);delta=player_eye-eye;distance=length(delta)
            weapon=prop(npc,'Weapon');ignore=[a for a in [npc,weapon] if valid(a)]
            hit=self.trace(eye,player_eye,ignore)
            facing=dot(npc.get_actor_forward_vector(),unit(u.Vector(delta.x,delta.y,0)))>.42
            visible=distance<2300 and facing and (hit is None or self.hit_actor(hit)==self.player)
            entry['seen']=entry['seen']+dt if visible else 0.
            hp=prop(npc,'Current HP',0.)
            if hp<entry['hp']:entry['last']=vec_copy(player_pos);entry['alert']=self.clock+6
            entry['hp']=hp
            if visible:entry['last']=vec_copy(player_pos);entry['alert']=self.clock+7
            elif distance<2400 and self.pc.is_input_key_down(self.input_keys['LeftMouseButton']):
                entry['last']=vec_copy(player_pos);entry['alert']=self.clock+5
            active=entry['alert']>self.clock and entry['last'] is not None
            destination=entry['last'] if active else entry['home']+u.Vector(math.sin(self.clock*.17+index)*180,math.cos(self.clock*.17+index)*180,0)
            direction=unit(u.Vector(destination.x-pos.x,destination.y-pos.y,0))
            look=u.MathLibrary.find_look_at_rotation(eye,player_eye if visible else destination+u.Vector(0,0,60))
            current=npc.get_actor_rotation()
            diff=(look.yaw-current.yaw+180)%360-180
            npc.set_actor_rotation(u.Rotator(yaw=current.yaw+max(-120*dt,min(120*dt,diff))),False)
            controller=npc.get_controller()
            if controller:controller.set_control_rotation(look)
            for cam in npc.get_components_by_class(u.CameraComponent):
                cam.use_pawn_control_rotation=False
                cam.set_world_rotation(u.MathLibrary.find_look_at_rotation(cam.get_world_location(),player_eye if visible else destination+u.Vector(0,0,60)),False,True)
            if visible and entry['seen']>.45 and abs(diff)<12 and self.ai_damage_enabled and self.clock>=entry['next_fire'] and valid(weapon):
                entry['burst']+=1
                entry['next_fire']=self.clock+(.28 if entry['burst']%3 else 1.3+index*.07)
                weapon.call_method('Start Firing');weapon.call_method('Stop Firing');self.shots_fired+=1
            entry['move']=u.Vector()
            if not visible or distance>950:
                obstacle=self.trace(pos,pos+direction*140,ignore,radius=30)
                if obstacle:
                    right=u.Vector(-direction.y,direction.x,0)*entry['side']
                    if self.trace(pos,pos+right*160,ignore,radius=30):entry['side']*=-1
                    direction=right
                entry['move']=direction

    def update(self,dt,keys=None):
        if not valid(self.player):return
        dt=min(dt,.1);self.clock+=dt
        keys=self.keys() if keys is None else keys
        self.loot.update(dt,keys)
        self.stance.update(dt,keys)
        self.update_camera(dt,keys)
        self.update_trigger(keys)
        self.ai_time+=dt
        if self.ai_time>=.10:self.update_ai(self.ai_time);self.ai_time=0
        if self.ai_enabled:
            for entry in self.enemies:
                if valid(entry['actor']) and not entry['dead']:entry['actor'].add_movement_input(entry['move'],.7,True)
        self.feedback.update(dt)
        self.audio.update(dt);self.pmc.update();self.weapon_visual.update()
        self.optic.update()
        self.hud_time+=dt
        if self.hud_time>=.12:
            self.hud_time=0;self.draw_hud()
        self.previous=set(keys)

    def draw_hud(self):
        if self.inventory:
            u.SystemLibrary.print_string(self.world,'',True,False,u.LinearColor(1,1,1,1),.01,'FactoryTacticalHUD');return
        lines=[('破冰船' if self.is_icebreaker else '工厂')+' / 战术预览    Q/E 侧倾  |  右键 瞄准  |  F 搜刮  |  Tab 背包']
        hp=prop(self.player,'Current HP')
        if hp is not None:lines.append('生命 %.0f    击倒 %d    背包 %d 件'%(hp,self.kills,len(self.pack)))
        rounds=prop(self.weapon,'Current Bullets')
        if rounds is not None:lines.append('弹药 %d  |  1/2 选择武器 · X 切枪 · C 蹲下 · Z 趴下 · R 装填栓动步枪  |  %s'%(rounds,{'stand':'站立','crouch':'蹲姿','prone':'卧姿'}[self.stance.mode]))
        if self.inventory:
            lines.append('—— 背包 6 × 5 ——')
            for item in self.pack:lines.append('%s  [%d×%d]   %.1f kg'%(item['name'],item['w'],item['h'],item['kg']))
            lines.append('再按 Tab 关闭；战局不会暂停')
        elif self.search:lines.append('正在搜索 %s … %d%%'%(self.search['title'],min(100,self.search_time*50)))
        elif self.focus:lines.append('[F] 搜刮 '+self.focus['title'])
        if self.clock<self.message_until:lines.append(self.message)
        u.SystemLibrary.print_string(self.world,'\n'.join(lines),True,False,u.LinearColor(.78,.87,.71,1),.3,'FactoryTacticalHUD')
