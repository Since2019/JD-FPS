"""Enable the tactical controller when this project's tactical map enters PIE."""
import unreal as u
import os, sys, traceback
_tools=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../Tools'))
_command=u.SystemLibrary.get_command_line().lower()
if '-run=' not in _command and '-executepythonscript=' not in _command:
    if _tools not in sys.path:sys.path.insert(0,_tools)
    from tactical_runtime import TacticalSession
    _session=None
    def _factory_tick(dt):
        global _session
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world or not any(name in world.get_name() for name in ['ClassicFactoryTactical','ClassicFactoryVisual','Icebreaker']):
            _session=None;return
        player=u.GameplayStatics.get_player_character(world,0)
        if not player:return
        try:
            if _session is None or _session.player!=player:_session=TacticalSession(world,player)
            _session.update(dt)
        except Exception:
            u.log_error(traceback.format_exc())
            u.unregister_slate_post_tick_callback(_factory_handle)
    _factory_handle=u.register_slate_post_tick_callback(_factory_tick)
