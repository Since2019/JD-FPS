"""Event-driven first-person foley and positional combat sound."""
from runtime_objects import valid
import unreal as u,random,math
class CombatAudio:
    def __init__(self,session):
        self.s=session;self.rng=random.Random(410);self.events={};self.components=[];self.last_step={};self.last_ads=False;self.last_search=False;self.last_inventory=False
        self.sounds={n:u.load_asset('/Game/Factory/Audio/'+n) for n in ['Step_Concrete','Gear_Cloth','Impact_Metal','Search_Latch']}
        self.sounds['shot']=u.load_asset('/Game/Factory/Audio/Rifle_Shot') or u.load_asset('/Game/Weapons/GrenadeLauncher/Audio/FirstPersonTemplateWeaponFire02')
        self.attenuation=u.load_asset('/Game/Factory/Audio/CombatAttenuation')
        assert all(self.sounds.values()) and self.attenuation
    def play(self,name,location=None,volume=1.,pitch=1.):
        if location is None:component=u.GameplayStatics.spawn_sound2d(self.s.world,self.sounds[name],volume_multiplier=volume,pitch_multiplier=pitch)
        else:component=u.GameplayStatics.spawn_sound_at_location(self.s.world,self.sounds[name],location,volume_multiplier=volume,pitch_multiplier=pitch,attenuation_settings=self.attenuation)
        if component:
            self.events[name]=self.events.get(name,0)+1;self.components.append(component)
        return component
    def shot(self,weapon,player):
        pos=None if player else weapon.get_actor_location()
        self.play('shot',pos,.72 if player else .55,self.rng.uniform(.96,1.035))
    def update(self,dt):
        self.components=[c for c in self.components if valid(c)]
        aiming=self.s.ads>.45
        if aiming!=self.last_ads:self.play('Gear_Cloth',volume=.28);self.last_ads=aiming
        searching=self.s.search is not None
        if searching and not self.last_search:self.play('Search_Latch',volume=.48)
        self.last_search=searching
        if self.s.inventory!=self.last_inventory:self.play('Gear_Cloth',volume=.35);self.last_inventory=self.s.inventory
        people=[(self.s.player,True)]+[(e['actor'],False) for e in self.s.enemies if not e['dead']]
        for actor,player in people:
            if not valid(actor):continue
            v=actor.get_velocity();speed=math.hypot(v.x,v.y)
            if speed<35 or actor.character_movement.is_falling():continue
            interval=max(.27,min(.59,125/max(speed,1)))
            if self.s.clock-self.last_step.get(actor,-1)>interval:
                self.last_step[actor]=self.s.clock
                self.play('Step_Concrete',None if player else actor.get_actor_location(),.7 if player else .55,self.rng.uniform(.91,1.09))
