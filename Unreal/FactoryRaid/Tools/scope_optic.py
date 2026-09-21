"""Weapon-mounted etched reticle, never a screen-centre overlay."""
import unreal as u
class ScopeOptic:
    def __init__(self,session):
        self.s=session;self.parts=[];self.crosshair_removed=False
        gun=next(c for c in session.weapon.get_components_by_class(u.SkeletalMeshComponent) if c.get_name()=='FP_Weapon')
        api=u.get_default_object(u.GameplayStatics)
        for name,material in [('OPT_Housing','M_OpticBody'),('OPT_Hardware','M_OpticMetal'),('OPT_Reticle','M_SpecterReticle')]:
            tf=u.Transform()
            actor=api.call_method('BeginDeferredActorSpawnFromClass',args=(session.world,u.StaticMeshActor.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,session.player,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            actor=api.call_method('FinishSpawningActor',args=(actor,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            c=actor.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE)
            c.set_static_mesh(u.load_asset('/Game/Factory/Visual2/PMC/'+name));c.set_material(0,u.load_asset('/Game/Factory/Visual2/Optics/'+material));c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);c.set_cast_shadow(False)
            actor.attach_to_component(gun,'',u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.KEEP_WORLD,False)
            actor.root_component.set_relative_location(u.Vector(0,0,-3.5),False,True)
            actor.tags=[u.Name('FactoryOptic')];self.parts.append(actor)
        self.widget_library=u.get_default_object(u.load_class(None,'/Script/UMG.WidgetBlueprintLibrary'))
        self.widget_class=u.load_class(None,'/Game/Variant_Shooter/UI/UI_Shooter.UI_Shooter_C')
        self.ui_report=[];self.ui_check_at=0.;self.remove_screen_reticle()
        tf=u.Transform()
        self.capture_actor=api.call_method('BeginDeferredActorSpawnFromClass',args=(session.world,u.SceneCapture2D.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,session.player,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        self.capture_actor=api.call_method('FinishSpawningActor',args=(self.capture_actor,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        self.capture=self.capture_actor.get_component_by_class(u.SceneCaptureComponent2D)
        self.capture.capture_every_frame=False;self.capture.capture_on_movement=False
        self.capture.always_persist_rendering_state=True
        self.capture.capture_source=u.SceneCaptureSource.SCS_SCENE_COLOR_HDR
        self.capture.fov_angle=25.55
        self.target=u.RenderingLibrary.create_render_target2d(session.world,512,512,u.TextureRenderTargetFormat.RTF_RGBA16F)
        self.capture.texture_target=self.target
        self.capture.hidden_actors=[session.player,session.weapon]+self.parts+session.weapon_visual.player_parts
        self.lens=self.parts[-1].static_mesh_component.create_dynamic_material_instance(0,u.load_asset('/Game/Factory/Visual2/Optics/M_SpecterLens'))
        self.lens.set_texture_parameter_value('ScopeView',self.target)
        self.etched=u.load_asset('/Game/Factory/Visual2/Optics/M_SpecterReticle');self.lens_active=None
        self.specter_parts=list(self.parts);self.specter_lens=self.parts[-1];self.variant='MK18'
        actor=api.call_method('BeginDeferredActorSpawnFromClass',args=(session.world,u.StaticMeshActor.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,session.player,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        actor=api.call_method('FinishSpawningActor',args=(actor,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        c=actor.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_static_mesh(u.load_asset('/Game/Game/Assets/Models/Weapons/EOTechXPS3Scope/EOTechXPS3'));c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);c.set_cast_shadow(False)
        actor.attach_to_component(gun,'',u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.SNAP_TO_TARGET,u.AttachmentRule.KEEP_WORLD,False)
        # Manufacturer envelope 9.65 x 5.33 x 6.35 cm; imported bounds
        # 327.81253 x 203.44019 x 249.89731 cm. Keep window centre at Z=18.5.
        c.set_relative_scale3d(u.Vector(9.65/327.81253,5.33/203.44019,6.35/249.89731));c.set_relative_rotation(u.Rotator(yaw=90),False,True);c.set_relative_location(u.Vector(0,4,18.5-71.27*6.35/249.89731),False,True)
        self.holo=actor;self.holo_gun=gun;self.holo_material=c.create_dynamic_material_instance(1,u.load_asset('/Game/Factory/HK416/M_Holographic'));self.parts.append(actor);actor.set_actor_hidden_in_game(True)
        # Material/transform updates can recreate the component's physics state.
        # Disable collision at actor level as well as using a persistent profile.
        for part in self.parts:
            part.static_mesh_component.set_collision_profile_name('NoCollision')
            part.set_actor_enable_collision(False)
        self.bolt_lens=session.weapon_visual.bolt.scope.static_mesh_component.create_dynamic_material_instance(1,u.load_asset('/Game/Realism/WeaponTerrain/M_BoltLens'))
        self.bolt_lens.set_texture_parameter_value('ScopeView',self.target)
        self.update()
    def select(self,entry):
        self.variant='HK416' if entry and entry['name']=='HK416' else 'BOLT' if entry and entry['name']=='7.62 栓动步枪' else 'MK18'
        for a in self.specter_parts:a.set_actor_hidden_in_game(not entry or self.variant!='MK18')
        self.holo.set_actor_hidden_in_game(not entry or self.variant!='HK416')
        for part in self.parts:part.set_actor_enable_collision(False)
    def remove_screen_reticle(self):
        self.s.pc.show_mouse_cursor=self.s.inventory
        hud=self.s.pc.get_hud()
        if hud:
            try:hud.set_editor_property('show_hud',False)
            except Exception:pass
        widgets=self.widget_library.call_method('GetAllWidgetsOfClass',args=(self.s.world,self.widget_class,False))
        for widget in widgets:
            widget.call_method('SetRenderOpacity',args=(0.,))
            widget.call_method('RemoveFromParent')
        self.crosshair_removed=True
        self.ui_report=['Template HUD detached; native cursor hidden']
        self.ui_check_at=self.s.clock+.20
    def update(self):
        s=self.s
        if s.clock>=self.ui_check_at:self.remove_screen_reticle()
        if self.variant=='BOLT':
            tf=self.holo_gun.get_world_transform();v=tf.transform_location(u.Vector(0,0,18.5));self.bolt_lens.set_vector_parameter_value('Center',u.LinearColor(v.x,v.y,v.z,0))
            for name,axis in [('Right',u.Vector(1,0,0)),('Up',u.Vector(0,0,1))]:
                v=(tf.transform_location(axis)-tf.translation).normal();self.bolt_lens.set_vector_parameter_value(name,u.LinearColor(v.x,v.y,v.z,0))
            self.bolt_lens.set_scalar_parameter_value('Active',1. if s.ads>.5 else 0.)
            if s.ads>.5:
                self.capture.fov_angle=2.15
                self.capture_actor.set_actor_location(s.camera.get_world_location(),False,True);self.capture_actor.set_actor_rotation(s.camera.get_world_rotation(),False);self.capture.capture_scene()
            return
        if self.variant=='HK416':
            tf=self.holo_gun.get_world_transform()
            for name,axis in [('Forward',u.Vector(0,1,0)),('Right',u.Vector(1,0,0)),('Up',u.Vector(0,0,1))]:
                v=tf.transform_location(axis)-tf.translation;v=v.normal()
                self.holo_material.set_vector_parameter_value(name,u.LinearColor(v.x,v.y,v.z,0))
            return
        if s.ads<.01:
            # Preserve a clear etched surface in the hip view; no secondary scene cost.
            if self.lens_active is not False:self.specter_lens.static_mesh_component.set_material(0,self.etched);self.lens_active=False
            return
        if self.lens_active is not True:self.specter_lens.static_mesh_component.set_material(0,self.lens);self.lens_active=True
        self.capture.fov_angle=25.55
        self.capture_actor.set_actor_location(s.camera.get_world_location(),False,True)
        self.capture_actor.set_actor_rotation(s.camera.get_world_rotation(),False)
        self.capture.capture_scene()
