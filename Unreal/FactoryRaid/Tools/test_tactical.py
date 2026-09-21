import unreal as u, os, sys, time, json, traceback
TOOLS=os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:sys.path.insert(0,TOOLS)
from tactical_runtime import TacticalSession,prop,valid,length
u.EditorPythonScripting.set_keep_python_script_alive(True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
level.load_level('/Game/Factory/Maps/ClassicFactoryVisual')
session=None;phase=0;elapsed=0.;total=time.monotonic();report={'passed':False,'checks':[]};old_count=0;enemy_hp=0.;player_hp=0.
def check(condition,message):
    if not condition:raise AssertionError(message)
    report['checks'].append(message)
def finish():
    open(os.path.join(TOOLS,'tactical_test.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2))
    u.unregister_slate_post_tick_callback(callback)
    level.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def aim_at(point):
    session.pc.set_control_rotation(u.MathLibrary.find_look_at_rotation(session.camera.get_world_location(),point))
def place_for_box(box):
    p=box['actor'].get_actor_location();session.player.set_actor_location(u.Vector(p.x,p.y+140,p.z+33),False,True)
    session.player.character_movement.stop_movement_immediately()
    # Update the component to its new parent transform before calculating the sight line.
    session.update_camera(.1,set());aim_at(p)
def tick(dt):
    global phase,elapsed,session,old_count,enemy_hp,player_hp
    try:
        if time.monotonic()-total>120:raise RuntimeError('Tactical test timeout')
        elapsed+=min(dt,.1)
        if phase==0:level.editor_request_begin_play();phase=1;elapsed=0;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        player=u.GameplayStatics.get_player_character(world,0)
        if not player:return
        if session is None:
            if elapsed<2:return
            session=TacticalSession(world,player,True);session.ai_enabled=False
            check(isinstance(session.keys(),set),'Native UE keyboard and mouse state polling works')
            report['enemy_count']=len(session.enemies)
            report['animation_instances']=[{'mesh':c.get_name(),'anim':str(c.get_anim_instance()),'Is Aiming':prop(c.get_anim_instance(),'Is Aiming')} for c in player.get_components_by_class(u.SkeletalMeshComponent)]
            report['npc_actors']=[{'name':a.get_name(),'tags':str(a.tags)} for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor) if 'NPC' in a.get_class().get_name()]
            check(len(session.enemies)==6,'Six enemy characters are present')
            report['enemy_initial_hp']=[prop(e['actor'],'Current HP') for e in session.enemies]
            report['enemy_weapon']=[str(prop(e['actor'],'Weapon')) for e in session.enemies]
            check(valid(prop(player,'Current Weapon')),'Player has a working weapon')
            phase=2;elapsed=0
        if phase==2:
            session.update(dt,{'Q'})
            if elapsed>.7:
                check(session.lean<-15 and session.camera.get_world_location().y<player.get_actor_location().y-15,'Q physically moves the eye left')
                check(session.camera.get_world_rotation().roll<-5,'Q tilts left, matching its displacement')
                phase=3;elapsed=0
        elif phase==3:
            session.update(dt,{'E'})
            if elapsed>.7:
                check(session.lean>15 and session.camera.get_world_location().y>player.get_actor_location().y+15,'E physically moves the eye right')
                check(session.camera.get_world_rotation().roll>5,'E tilts right, matching its displacement')
                phase=4;elapsed=0
        elif phase==4:
            session.update(dt,{'RightMouseButton'})
            if elapsed>.8:
                report['aim_state']={'alpha':session.ads,'fov':session.camera.field_of_view,'anim_available':session.anim_has_ads,'aiming':prop(session.anim,'Is Aiming')}
                check(abs(session.camera.field_of_view-90)<.01,'ADS preserves world FOV instead of zooming')
                report['sights']={'rear_error_cm':session.aim_error,'axis_alignment':session.sight_alignment}
                check(session.aim_error<.2 and session.sight_alignment>.999,'Rear sight and front post align with the actual camera ray')
                check(prop(session.weapon,'Firing Montage') is None and prop(session.weapon,'Firing Recoil')==0,'Single smooth pose and recoil controller replaces competing template effects')
                player.set_actor_location(u.Vector(-1800,3158,98),False,True);player.set_actor_rotation(u.Rotator(0,0,0),False);session.pc.set_control_rotation(u.Rotator(0,0,0));phase=5;elapsed=0
        elif phase==5:
            session.update(dt,{'E'})
            if elapsed>.8:
                check(abs(session.lean)<2,'Wall prevents camera clipping while leaning')
                place_for_box(session.boxes[0]);old_count=len(session.pack);phase=6;elapsed=0
        elif phase==6:
            session.update(dt,{'F'})
            if elapsed>.6:
                b=session.boxes[0];p=b['actor'].get_actor_location();eye=session.camera.get_world_location();hit=session.trace(eye,p)
                report['search_debug']={'box':b['title'],'position':str(p),'player':str(player.get_actor_location()),'eye':str(eye),'control':str(session.pc.get_control_rotation()),'forward':str(session.camera.get_forward_vector()),'focus':session.focus['title'] if session.focus else None,'hit':str(session.hit_actor(hit)),'impact':str(session.hit_point(hit)),'elapsed':session.search_time}
                check(session.search is not None,'Visible nearby container can be searched')
                session.update(.02,set());check(session.search is None and len(session.pack)==old_count,'Releasing F interrupts without granting loot');phase=7;elapsed=0
        elif phase==7:
            session.update(dt,{'F'})
            if elapsed>2.3:
                check(len(session.pack)==old_count+1 and session.boxes[0]['searched'],'Holding F transfers loot once to inventory')
                phase=8;elapsed=0
        elif phase==8:
            session.update(dt,{'F'})
            if elapsed>.4:
                check(len(session.pack)==old_count+1,'Searched container cannot duplicate loot')
                player.set_actor_location(u.Vector(-2800,2500,98),False,True)
                enemy=session.enemies[0]['actor'];enemy.set_actor_location(u.Vector(-2300,2500,98),False,True)
                session.update_camera(.1,set());aim_at(enemy.get_actor_location()+u.Vector(0,0,45))
                enemy_hp=prop(enemy,'Current HP');session.weapon=prop(player,'Current Weapon');phase=9;elapsed=0
        elif phase==9:
            session.update(dt,set())
            if elapsed>.25:session.weapon.call_method('Start Firing');phase=10;elapsed=0
        elif phase==10:
            session.update(dt,set())
            if elapsed>1.:
                session.weapon.call_method('Stop Firing')
                enemy=session.enemies[0]['actor'];remaining=prop(enemy,'Current HP',0)
                report['enemy_hp_before']=enemy_hp;report['enemy_hp_after']=remaining
                check(not valid(enemy) or remaining<enemy_hp,'Player projectiles damage an enemy')
                # Use a fresh guard to test its real projectile path back to the player.
                enemy=session.enemies[1]['actor'];enemy.set_actor_location(u.Vector(-2300,2500,98),False,True)
                enemy.set_actor_rotation(u.Rotator(yaw=180),False)
                session.enemies[1]['next_fire']=0;session.ai_enabled=True;player_hp=prop(player,'Current HP');phase=11;elapsed=0
        elif phase==11:
            session.update(dt,set())
            if elapsed>2.:
                check(session.shots_fired>0,'Enemy acquires player and fires its weapon')
                after=prop(player,'Current HP');report['player_hp_before']=player_hp;report['player_hp_after']=after
                check(after is not None and after<player_hp,'Enemy projectiles damage the player')
                report['feedback']={'flashes':session.feedback.flashes,'impacts':session.feedback.impacts}
                check(session.feedback.flashes>0,'Muzzle feedback is triggered by actual ammunition consumption')
                session.ai_damage_enabled=False
                # A guard with the player behind it must not gain visual contact.
                entry=session.enemies[1];entry['actor'].set_actor_rotation(u.Rotator(yaw=0),False);entry['seen']=0.;entry['alert']=0.;entry['last']=None
                session.update_ai(.1)
                check(entry['seen']==0.,'Enemy cannot see the player behind its back')
                entry['actor'].set_actor_rotation(u.Rotator(yaw=180),False);entry['seen']=0.;entry['next_fire']=0
                session.ai_damage_enabled=True;old_shots=session.shots_fired
                session.update_ai(.1)
                check(entry['seen']<=.11 and session.shots_fired==old_shots,'Enemy visual acquisition has a reaction delay')
                session.ai_enabled=False
                session.pc.set_control_rotation(u.Rotator(pitch=-45,yaw=-90))
                phase=12;elapsed=0
        elif phase==12:
            session.update(dt,{'RightMouseButton'})
            if elapsed>.5:session.weapon.call_method('Start Firing');phase=13;elapsed=0
        elif phase==13:
            session.update(dt,{'RightMouseButton'})
            bullets=u.GameplayStatics.get_all_actors_of_class(world,session.feedback.cls)
            for b in bullets:
                movement=b.get_component_by_class(u.ProjectileMovementComponent)
                if movement:
                    report['projectile_speed']=movement.initial_speed
                    report['projectile_mesh_hidden']=all(m.hidden_in_game for m in b.get_components_by_class(u.StaticMeshComponent))
            if elapsed>.5:
                session.weapon.call_method('Stop Firing')
                check(report.get('projectile_speed',0)>=70000,'Rifle rounds use high-speed swept projectile movement')
                check(report.get('projectile_mesh_hidden',False),'Template foam dart mesh is hidden')
                check(session.feedback.impacts>0,'Real projectile impacts produce surface marks')
                report['feedback']={'flashes':session.feedback.flashes,'impacts':session.feedback.impacts}
                report['passed']=True;finish()
    except Exception:
        report['error']=traceback.format_exc();report['phase']=phase;finish()
callback=u.register_slate_post_tick_callback(tick)
