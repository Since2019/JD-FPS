"""UE Python wrappers may outlive their UObject after actor destruction/GC."""
import unreal as u

def valid(obj):
    if obj is None:return False
    try:return u.SystemLibrary.is_valid(obj)
    except (TypeError,ReferenceError):return False
