import unreal as u, os, sys, time, traceback
TOOLS=os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:sys.path.insert(0,TOOLS)
from tactical_runtime import TacticalSession
u.EditorPythonScripting.set_keep_python_script_alive(True)
level=u.get_editor_subsystem(u.LevelEditorSubsystem)
level.load_level('/Game/Factory/Maps/ClassicFactoryVisual')
u.get_default_object(u.load_class(None,'/Script/UnrealEd.LevelEditorPlaySettings')).set_editor_property('EnableGameSound',True)
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'au.ForcePieClientsToShareAudio 1')
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'au.DisableAppVolume 1')
session=None;requested=False;had_game=False;started=time.monotonic()
def tick(dt):
    global session,requested,had_game
    try:
        if not requested:level.editor_request_begin_play();requested=True;return
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:
            if had_game:
                u.unregister_slate_post_tick_callback(callback)
                u.EditorPythonScripting.set_keep_python_script_alive(False)
            return
        player=u.GameplayStatics.get_player_character(world,0)
        if not player:return
        had_game=True
        if session is None or session.player!=player:
            session=TacticalSession(world,player)
            u.log('Factory tactical ready: %d enemies, %d containers, aiming=%s'%(len(session.enemies),len(session.boxes),session.anim_has_ads))
        session.update(dt)
    except Exception:
        open(os.path.join(TOOLS,'tactical_runtime_error.txt'),'w',encoding='utf-8').write(traceback.format_exc())
        u.log_error(traceback.format_exc())
        u.unregister_slate_post_tick_callback(callback)
        level.editor_request_end_play()
        u.EditorPythonScripting.set_keep_python_script_alive(False)
callback=u.register_slate_post_tick_callback(tick)
