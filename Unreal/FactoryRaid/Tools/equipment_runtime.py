"""Inventory drag controller and equipped item state for the MK18 prototype."""
import unreal as u,math,copy
from item_icons import texture as item_texture
from loot_model import item,move,SLOTS,fits,accepts

class Equipment:
    def __init__(self,loot):
        self.loot=loot;self.s=loot.s;self.slots=dict.fromkeys(SLOTS);self.selected='primary1';self.loaded=None;self.helmet=None;self.helmet_parts=[];self.drag=None;self.suppress_until=-1.;self.ready_at=0
        rifle=item('HK416');rifle['ammo']=30;rifle['optic']='EOTech XPS3';self.slots['primary1']=rifle
        self.slots['primary2']=item('7.62 栓动步枪');self.slots['primary2']['ammo']=5
        self.buttons={};self.labels={};self.slot_icons={};self.sync()
    def sync(self):
        s=self.s;entry=self.slots[self.selected]
        if self.loaded is not entry:
            s.weapon.call_method('Stop Firing');s.trigger_active=False
            s.bolt_reload_until=0
            if self.loaded:self.loaded['ammo']=self.loaded.get('bolt_ammo',s.prop(s.weapon,'Current Bullets',0)) if self.loaded['name']=='7.62 栓动步枪' else s.prop(s.weapon,'Current Bullets',0)
            self.loaded=entry;ammo=entry.setdefault('ammo',5 if entry['name']=='7.62 栓动步枪' else 30) if entry else 0
            if entry and entry['name']=='7.62 栓动步枪':ammo=entry.setdefault('bolt_ammo',max(0,min(5,ammo)))
            s.weapon.set_editor_property('Current Bullets',ammo);s.rounds_seen=ammo;s.feedback.ammo[s.weapon]=ammo
            s.recoil=s.recoil_velocity=s.kick=s.kick_velocity=0.;self.ready_at=s.clock+.35
        hidden=entry is None
        s.fp_mesh.set_visibility(not hidden,True)
        s.weapon_visual.select(entry);s.optic.select(entry)
        if self.helmet is not self.slots['head']:
            for actor in self.helmet_parts:
                s.pmc.parts=[p for p in s.pmc.parts if p[1]!=actor];actor.destroy_actor()
            self.helmet_parts=[];self.helmet=self.slots['head']
            if self.helmet:
                for mesh,material in [('FAST_Shell','M_PMC_Helmet'),('FAST_Hardware','M_FAST_Hardware'),('FAST_Loop','M_FAST_Loop'),('FAST_Straps','M_FAST_Straps')]:
                    actor=s.pmc.part(s.player,s.player.mesh,'head',mesh,(3,0,15),material);actor.static_mesh_component.set_owner_no_see(True);self.helmet_parts.append(actor)
            s.optic.capture.hidden_actors=[s.player,s.weapon]+s.optic.parts+s.weapon_visual.player_parts+self.helmet_parts
    def build(self,tree):
        self.canvas=u.find_object(tree,'LootCanvas')
        for name in ['HeadSlot','HeadSlotText','VestSlot','VestSlotText','WeaponSlot','WeaponSlotText']:
            u.find_object(tree,name).set_visibility(u.SlateVisibility.COLLAPSED)
        for index,key in enumerate(SLOTS):
            b=u.new_object(u.Button,tree,'Equip_'+key);b.set_editor_property('is_focusable',False)
            slot=self.canvas.add_child_to_canvas(b);slot.set_position(u.Vector2D(48+index*184,154));slot.set_size(u.Vector2D(178, 76))
            content=u.new_object(u.Overlay,tree,'EquipContent_'+key);b.add_child(content);content.get_editor_property('slot').set_horizontal_alignment(u.HorizontalAlignment.H_ALIGN_FILL);content.get_editor_property('slot').set_vertical_alignment(u.VerticalAlignment.V_ALIGN_FILL)
            fit=u.new_object(u.ScaleBox,tree,'EquipFit_'+key);fit.set_stretch(u.Stretch.SCALE_TO_FIT);icon=u.new_object(u.Image,tree,'EquipIcon_'+key);fit.add_child(icon);slot=content.add_child_to_overlay(fit);slot.set_horizontal_alignment(u.HorizontalAlignment.H_ALIGN_FILL);slot.set_vertical_alignment(u.VerticalAlignment.V_ALIGN_FILL);slot.set_padding(u.Margin(4,31,4,2));self.slot_icons[key]=icon
            t=u.new_object(u.TextBlock,tree,'EquipText_'+key);font=t.get_editor_property('font');font.set_editor_property('size',11);t.set_font(font);slot=content.add_child_to_overlay(t);slot.set_vertical_alignment(u.VerticalAlignment.V_ALIGN_TOP)
            self.buttons[key]=b;self.labels[key]=t
            self.bind(b,key,0)
        for side in ['Pack','Loot']:
            for index in range(30):self.bind(self.loot.widgets[f'{side}Item{index}'],side,index)
        self.s.stance.build_buttons(tree,self.canvas,self.loot.bindings)
        self.ghost=u.new_object(u.Border,tree,'DragPreview');self.ghost.set_brush_color(u.LinearColor(.21,.29,.18,.85));self.canvas.add_child_to_canvas(self.ghost).set_z_order(100)
        self.ghost_text=u.new_object(u.TextBlock,tree,'DragCaption');font=self.ghost_text.get_editor_property('font');font.set_editor_property('size',16);self.ghost_text.set_font(font);self.ghost.add_child(self.ghost_text);self.ghost.set_visibility(u.SlateVisibility.COLLAPSED)
        self.ghost.remove_child(self.ghost_text)
        overlay=u.new_object(u.Overlay,tree,'DragContent');self.ghost.add_child(overlay)
        self.ghost_icon=u.new_object(u.Image,tree,'DragImage');fit=u.new_object(u.ScaleBox,tree,'DragImageFit');fit.set_stretch(u.Stretch.SCALE_TO_FIT);fit.add_child(self.ghost_icon)
        slot=overlay.add_child_to_overlay(fit);slot.set_horizontal_alignment(u.HorizontalAlignment.H_ALIGN_FILL);slot.set_vertical_alignment(u.VerticalAlignment.V_ALIGN_FILL);slot.set_padding(u.Margin(4,25,4,4));overlay.add_child_to_overlay(self.ghost_text)
        self.drop_preview=u.new_object(u.Border,tree,'DropPreview');slot=self.canvas.add_child_to_canvas(self.drop_preview);slot.set_z_order(90);self.drop_preview.set_visibility(u.SlateVisibility.COLLAPSED)
    def bind(self,button,side,index):
        def pressed():self.begin(side,index)
        def released():self.release()
        self.loot.bindings.extend([pressed,released]);button.on_pressed.add_callable(pressed);button.on_released.add_callable(released)
        if side in ('primary1','primary2'):
            def clicked():
                if self.s.clock>=self.suppress_until:self.select(side)
            self.loot.bindings.append(clicked);button.on_clicked.add_callable(clicked)
    def select(self,slot):
        self.selected=slot;self.sync()
        self.s.say(('主武器 1' if slot=='primary1' else '主武器 2')+('：'+self.loaded['name'] if self.loaded else '：空槽，请先装备步枪'))
        if self.s.inventory:self.loot.draw()
    def pointer(self):
        # Slate owns captured button drags: PlayerController's cached mouse stops
        # updating until release. Convert the live desktop cursor through the real
        # game viewport, not the Python WidgetTree's uncached child geometry.
        layout=u.get_default_object(u.load_class(None,'/Script/UMG.WidgetLayoutLibrary'))
        slate=u.get_default_object(u.load_class(None,'/Script/UMG.SlateBlueprintLibrary'))
        desktop=layout.call_method('GetMousePositionOnPlatform')
        pixel,_=slate.call_method('AbsoluteToViewport',args=(self.s.world,desktop))
        width,height=self.s.pc.get_viewport_size()
        if width<=0 or height<=0:return u.Vector2D(-10000,-10000)
        scale=min(width/1280.,height/720.)
        return u.Vector2D((pixel.x-(width-1280*scale)*.5)/scale,(pixel.y-(height-720*scale)*.5)/scale)
    def begin(self,side,index,point=None):
        source=side if side in SLOTS else self.s.pack if side=='Pack' else self.loot.active['items'] if self.loot.active else []
        entry=self.slots[source] if isinstance(source,str) else source[index] if index<len(source) else None
        if not entry or not entry.get('known',True):return
        # The controller retains the mouse-down position during Slate capture.
        # This is useful ONLY at drag start: rapid queued drags can already have
        # moved the live desktop cursor to the release point before OnPressed.
        if point is not None:p=point
        else:
            mouse=self.s.pc.get_mouse_position();width,height=self.s.pc.get_viewport_size();scale=min(width/1280.,height/720.)
            p=u.Vector2D((mouse[0]-(width-1280*scale)*.5)/scale,(mouse[1]-(height-720*scale)*.5)/scale) if mouse and scale>0 else self.pointer()
        # Preserve the precise grab point, rather than rounding it to a cell.
        if isinstance(source,str):
            offset=((p.x-(48+SLOTS.index(source)*184))/178*(entry['w']*86-2),(p.y-154)/76*(entry['h']*62-2))
        else:offset=(p.x-((48 if side=='Pack' else 664)+entry['x']*86),p.y-(282+entry['y']*62))
        self.drag={'source':source,'entry':entry,'start':p,'offset':offset,'moving':False}
        texture=item_texture(entry)
        if texture:self.ghost_icon.set_brush_from_texture(texture,True)
        self.ghost_icon.set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE if texture else u.SlateVisibility.COLLAPSED)
    def hover(self,p):
        if 154<=p.y<230 and 48<=p.x<600:
            index=int((p.x-48)/184)
            if index<3 and (p.x-48)%184<178:return SLOTS[index],None
        if 282<=p.y<592:
            for side,x in [('Pack',48),('Loot',664)]:
                if x<=p.x<x+516 and (side=='Pack' or self.loot.active):
                    return self.s.pack if side=='Pack' else self.loot.active['items'],(math.floor((p.x-x-self.drag['offset'][0])/86+.5),math.floor((p.y-282-self.drag['offset'][1])/62+.5))
        return None,None
    def release(self,point=None):
        if not self.drag:return
        d=self.drag;p=point or self.pointer()
        if (p-d['start']).length()>5:d['moving']=True
        if d['moving']:
            destination,pos=self.hover(p);ok=destination is not None and move(self.slots,d['source'],destination,d['entry'],pos)
            self.sync();self.suppress_until=self.s.clock+.2
            self.loot.say('已放置：'+d['entry']['name'] if ok else '无法放置：检查类型、边界或空余格子')
        self.cancel()
    def cancel(self):
        self.drag=None
        if hasattr(self,'ghost'):self.ghost.set_visibility(u.SlateVisibility.COLLAPSED)
        if hasattr(self,'drop_preview'):self.drop_preview.set_visibility(u.SlateVisibility.COLLAPSED)
    def update(self,keys):
        if not self.drag:
            if 'X' in keys and 'X' not in self.s.previous:self.s.stance.swap()
            for key,slot in [('One','primary1'),('Two','primary2')]:
                if key in keys and key not in self.s.previous:self.select(slot)
        if self.loaded:self.loaded['ammo']=self.s.prop(self.s.weapon,'Current Bullets',0)
        if self.drag:
            p=self.pointer();d=self.drag
            if (p-d['start']).length()>5:d['moving']=True
            if d['moving']:
                self.ghost.set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE);self.ghost_text.set_text(d['entry']['name']);slot=self.ghost.get_editor_property('slot');slot.set_position(u.Vector2D(p.x-d['offset'][0],p.y-d['offset'][1]));slot.set_size(u.Vector2D(d['entry']['w']*86-2,d['entry']['h']*62-2))
                destination,pos=self.hover(p)
                self.drop_preview.set_visibility(u.SlateVisibility.COLLAPSED)
                if destination is not None:
                    equipment,source,target,entry=copy.deepcopy((self.slots,d['source'],destination,d['entry']))
                    ok=move(equipment,source,target,entry,pos)
                    self.drop_preview.set_brush_color(u.LinearColor(*((.15,.55,.16,.35) if ok else (.7,.08,.05,.4))))
                    slot=self.drop_preview.get_editor_property('slot')
                    if isinstance(destination,str):location=(48+SLOTS.index(destination)*184,154);size=(178,76)
                    else:location=((48 if destination is self.s.pack else 664)+pos[0]*86,282+pos[1]*62);size=(entry['w']*86-2,entry['h']*62-2)
                    slot.set_position(u.Vector2D(*location));slot.set_size(u.Vector2D(*size));self.drop_preview.set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE)
    def draw(self):
        for key,t in self.labels.items():
            entry=self.slots[key];title={'head':'头部','primary1':'主武器 1','primary2':'主武器 2'}[key]
            detail=('FAST' if key=='head' else '%s · %d 发'%(entry['name'].replace(' 风格步枪',''),entry.get('ammo',30))) if entry else '拖入装备'
            t.set_text(title+(' · 使用中' if key==self.selected and entry else '')+'\n'+detail)
            icon=self.slot_icons[key];icon.set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE if entry else u.SlateVisibility.COLLAPSED)
            if entry and item_texture(entry):icon.set_brush_from_texture(item_texture(entry),True)
            self.buttons[key].set_background_color(u.LinearColor(*((.22,.29,.15,1) if key==self.selected and entry else (.08,.10,.08,1))))
