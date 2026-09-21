import unreal as u,os,sys,json,time,traceback,math,wave,array
TOOLS=os.path.dirname(__file__);sys.path.insert(0,TOOLS)
from tactical_runtime import TacticalSession,prop,length
u.EditorPythonScripting.set_keep_python_script_alive(True)
play_settings=u.get_default_object(u.load_class(None,'/Script/UnrealEd.LevelEditorPlaySettings'))
play_settings.set_editor_property('EnableGameSound',True)
play_settings.set_editor_property('SoloAudioInFirstPIEClient',True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem);level.load_level('/Game/Factory/Maps/ClassicFactoryVisual')
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'au.ForcePieClientsToShareAudio 1')
session=None;phase=0;elapsed=0.;began=time.monotonic();report={'passed':False};frames=[];capture=None
def finish():
    open(os.path.join(TOOLS,'presentation_test.json'),'w',encoding='utf-8').write(json.dumps(report,ensure_ascii=False,indent=2))
    u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(dt):
    global session,phase,elapsed,capture
    try:
        if time.monotonic()-began>150:raise RuntimeError('Presentation test timeout')
        elapsed+=min(dt,.1)
        if phase==0:level.editor_request_begin_play();phase=1;elapsed=0;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:return
        player=u.GameplayStatics.get_player_character(world,0)
        if not player:return
        if session is None:
            if elapsed<3:return
            session=TacticalSession(world,player,True);session.ai_enabled=False
            report['audio_cvars']={n:u.SystemLibrary.get_console_variable_int_value(n) for n in ['au.MuteAudio','au.DisableAppVolume','au.ForcePieClientsToShareAudio']}
            u.SystemLibrary.execute_console_command(world,'au.MuteAudio 0')
            u.SystemLibrary.execute_console_command(world,'au.DisableAppVolume 1')
            u.SystemLibrary.execute_console_command(world,'au.ClearMutesAndSolos')
            session.pc.set_control_rotation(u.Rotator(pitch=0,yaw=0));phase=2;elapsed=0
            u.AudioMixerLibrary.start_recording_output(world,10.)
        session.update(dt,{'RightMouseButton'} if phase in [3,4,5] else set())
        if phase==2 and elapsed>1.:
            report['pmc_count']=len(session.pmc.applied);report['gear_count']=len(session.pmc.parts)
            assert report['pmc_count']==6 and report['gear_count']>=72
            session.audio.play('Step_Concrete');session.audio.play('Search_Latch',volume=.4)
            phase=3;elapsed=0
        elif phase==3 and elapsed>1.:
            assert session.aim_error<.2
            phase=4;elapsed=0;session.weapon.call_method('Start Firing')
        elif phase==4:
            session.weapon.call_method('Start Firing')
            if 'audio_components' not in report and elapsed>.4:
                report['audio_components']=[{'playing':c.is_playing(),'volume':c.volume_multiplier,'sound':str(c.sound),'ui':c.is_ui_sound} for c in session.audio.components if u.SystemLibrary.is_valid(c)]
                u.SystemLibrary.execute_console_command(world,'au.DumpActiveSounds')
            frames.append({'dt':dt,'pitch':session.pc.get_control_rotation().pitch,'recoil':session.recoil,'kick':session.kick,'error':session.aim_error,'alignment':session.sight_alignment})
            if elapsed>1.5:session.weapon.call_method('Stop Firing');phase=5;elapsed=0
        elif phase==5 and elapsed>1.1:
            report['recoil_peak_deg']=max(f['recoil'] for f in frames)
            report['kick_peak_cm']=max(f['kick'] for f in frames)
            report['return_recoil_deg']=session.recoil
            report['max_sight_error_cm']=max(f['error'] for f in frames)
            report['max_frame_pitch_delta']=max(abs(frames[i]['pitch']-frames[i-1]['pitch']) for i in range(1,len(frames)))
            report['audio_events']=session.audio.events
            assert report['recoil_peak_deg']<.65
            assert report['max_frame_pitch_delta']<.35
            assert report['return_recoil_deg']<.01
            assert report['max_sight_error_cm']<.25
            assert session.audio.events.get('shot',0)>=8
            u.AudioMixerLibrary.stop_recording_output(world,u.AudioRecordingExportType.WAV_FILE,'combat_mix',TOOLS)
            npc=session.enemies[0]['actor'];npc.set_actor_location(u.Vector(-2450,2500,98),False,True);npc.set_actor_rotation(u.Rotator(yaw=180),False)
            report['gear_bounds']=[{'mesh':str(a.static_mesh_component.static_mesh),'bounds':str(a.static_mesh_component.get_local_bounds()),'scale':str(a.get_actor_scale3d()),'loc':str(a.get_actor_location())} for n,a in session.pmc.parts[:23]]
            api=u.get_default_object(u.GameplayStatics);tf=u.Transform()
            lamp=api.call_method('BeginDeferredActorSpawnFromClass',args=(world,u.PointLight.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            lamp=api.call_method('FinishSpawningActor',args=(lamp,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
            lamp.light_component.set_mobility(u.ComponentMobility.MOVABLE)
            lamp.set_actor_location(u.Vector(-2700,2450,240),False,True);lamp.light_component.set_intensity(4500.)
            session.pc.set_control_rotation(u.Rotator(pitch=-7,yaw=0));phase=6;elapsed=0
        elif phase==6 and elapsed>2.:
            if capture is None:capture=u.AutomationLibrary.take_high_res_screenshot(1280,720,os.path.join(TOOLS,'view_pmc.png'))
            if capture and capture.is_task_done():phase=7;elapsed=0
        elif phase==7 and elapsed>1.:
            with wave.open(os.path.join(TOOLS,'combat_mix.wav'),'rb') as recording:
                samples=array.array('h',recording.readframes(recording.getnframes()))
                report['audio_seconds']=recording.getnframes()/recording.getframerate()
            report['audio_peak']=max(abs(v) for v in samples)/32768.
            report['audio_rms']=(sum(float(v)*v for v in samples)/len(samples))**.5/32768.
            assert report['audio_rms']>.0005,'Rendered mix is silent'
            report['npc_weapons']=[str(prop(e['actor'],'Weapon').get_class().get_name()) for e in session.enemies]
            assert all('Rifle' in name for name in report['npc_weapons'])
            report['passed']=True;report['frames']=frames;finish()
    except Exception:report['error']=traceback.format_exc();report['phase']=phase;finish()
handle=u.register_slate_post_tick_callback(tick)
