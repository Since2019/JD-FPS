"""Grounded stance collision, smooth eye height and weapon transitions."""
import unreal as u,math

class Stance:
    def __init__(self,s):
        self.s=s;self.mode='stand';self.cap=s.player.capsule_component
        self.stand_half=self.cap.get_unscaled_capsule_half_height();self.radius=self.cap.get_unscaled_capsule_radius()
        self.eye=self.stand_half+s.eye_height;self.stand_eye=self.eye
        self.mesh_origin=s.player.mesh.get_editor_property('relative_location');self.mesh_rotation=s.player.mesh.get_editor_property('relative_rotation')
        self.alpha=0.;self.switch_alpha=0.
    def set(self,mode):
        if mode==self.mode:mode='stand'
        s=self.s
        if s.player.character_movement.is_falling():return False
        old=self.cap.get_unscaled_capsule_half_height()
        half={'stand':self.stand_half,'crouch':max(self.radius,62.),'prone':24.}[mode]
        radius=22. if mode=='prone' else self.radius
        foot=s.player.get_actor_location()-u.Vector(0,0,old);center=foot+u.Vector(0,0,half)
        if half>old:
            hit=u.SystemLibrary.capsule_trace_single(s.world,center+u.Vector(0,0,2),center+u.Vector(0,0,2.1),radius*.96,half-2,u.TraceTypeQuery.TRACE_TYPE_QUERY1,False,s.ignored(),u.DrawDebugTrace.NONE)
            if hit:s.say('上方空间不足，无法起身');return False
        self.cap.set_capsule_size(radius,half,True);s.player.set_actor_location(center,False,True)
        self.mode=mode;s.player.character_movement.max_step_height=12. if mode=='prone' else 35.
        s.say({'stand':'站立','crouch':'蹲下','prone':'趴下'}[mode]);return True
    def update(self,dt,keys):
        s=self.s
        if not s.inventory:
            for key,mode in [('C','crouch'),('Z','prone')]:
                if key in keys and key not in s.previous:self.set(mode)
        target={'stand':self.stand_eye,'crouch':100.,'prone':43.}[self.mode]
        self.eye+=(target-self.eye)*(1-math.exp(-12*dt));s.eye_height=self.eye-self.cap.get_unscaled_capsule_half_height()
        self.alpha+=((1 if self.mode=='prone' else 0)-self.alpha)*(1-math.exp(-9*dt))
        # Third-person body follows the low profile; arms remain in the ADS solver.
        s.player.mesh.set_relative_location(self.mesh_origin+u.Vector(0,0,self.stand_half-self.cap.get_unscaled_capsule_half_height()+18*self.alpha),False,True)
        low=u.Rotator(pitch=self.mesh_rotation.pitch, yaw=self.mesh_rotation.yaw,roll=self.mesh_rotation.roll-85)
        s.player.mesh.set_relative_rotation(u.MathLibrary.r_lerp(self.mesh_rotation,low,self.alpha,True),False,True)
        remaining=max(0,s.loot.equipment.ready_at-s.clock)
        self.switch_alpha=math.sin(min(1,remaining/.35)*math.pi) if remaining else 0.
    def build_buttons(self,tree,canvas,bindings):
        for index,(text,action) in enumerate([('1 / 2 · 切枪',self.swap),('C · 蹲下',lambda:self.set('crouch')),('Z · 趴下',lambda:self.set('prone'))]):
            b=u.new_object(u.Button,tree,'ActionButton'+str(index));b.set_editor_property('is_focusable',False)
            slot=canvas.add_child_to_canvas(b);slot.set_position(u.Vector2D(48+index*184,615));slot.set_size(u.Vector2D(178,30))
            t=u.new_object(u.TextBlock,tree,'ActionText'+str(index));font=t.get_editor_property('font');font.set_editor_property('size',14);t.set_font(font);t.set_text(text);b.add_child(t)
            bindings.append(action);b.on_clicked.add_callable(action)
    def swap(self):
        e=self.s.loot.equipment;e.select('primary2' if e.selected=='primary1' else 'primary1')
