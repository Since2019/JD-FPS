"""Native UMG inventory and persistent searchable ragdoll loot sources for editor PIE."""
import unreal as u,math
from loot_model import contents,transfer,item
from runtime_objects import valid
def distance(a,b):return (a-b).length()
class LootInterface:
    def __init__(self,s):
        self.s=s;self.active=None;self.widget=None;self.widgets={};self.bindings=[];self.reveal=0.;self.last_draw=0.;self.corpses=[];self.pending_physics=[];self.feedback='';self.feedback_until=0.
        for b in s.boxes:b['items']=contents(b['item']);b['corpse']=False
        for entry in s.pack:
            seed=item(entry['name'],entry['w'],entry['h'],entry['kg']);entry.update({k:v for k,v in seed.items() if k not in entry})
        for e in s.enemies:
            npc=e['actor'];e['last_location']=npc.get_actor_location();e['last_rotation']=npc.get_actor_rotation();e['body_mesh']=npc.mesh.get_editor_property('skeletal_mesh_asset');e['corpse_created']=False
        from equipment_runtime import Equipment
        self.equipment=Equipment(self)
        self.lib=u.get_default_object(u.load_class(None,'/Script/UMG.WidgetBlueprintLibrary'))
    def control(self,open):
        if self.s.inventory==open:return
        self.s.inventory=open;self.s.pc.set_ignore_move_input(open);self.s.pc.set_ignore_look_input(open)
        self.s.player.character_movement.stop_movement_immediately();self.s.weapon.call_method('Stop Firing');self.s.trigger_active=False
        self.s.pc.show_mouse_cursor=open
        if open:self.lib.call_method('SetInputMode_GameAndUIEx',args=(self.s.pc,None,u.MouseLockMode.DO_NOT_LOCK,False,False))
        else:self.lib.call_method('SetInputMode_GameOnly',args=(self.s.pc,False))
    def ensure_widget(self):
        if self.widget:return
        cls=u.load_class(None,'/Game/Factory/Visual4/UI/WBP_Loot_v2.WBP_Loot_v2_C');assert cls,'Loot UI assets not prepared'
        self.widget=self.lib.call_method('Create',args=(self.s.world,cls,self.s.pc))
        self.widget.call_method('AddToViewport',args=(100,))
        tree=next((o for o in u.ObjectIterator() if o.get_outer()==self.widget and o.get_class().get_name()=='WidgetTree'),None)
        assert tree,'Runtime widget children: '+str([str(o) for o in u.ObjectIterator() if o.get_outer()==self.widget])
        names=['RightTitle','SearchStatus','Weight','Feedback','SearchProgress','RightSection','HeadSlotText','TakeAll']+[f'{side}{part}{i}' for side in ['Pack','Loot'] for i in range(30) for part in ['Item','Text','Icon']]
        self.widgets={name:u.find_object(tree,name) for name in names};assert all(self.widgets.values()),'Missing UMG inventory widgets: '+str([n for n,v in self.widgets.items() if v is None])
        self.widgets['HeadSlotText'].set_text('头部\n未装备')
        self.icon_fits=[]
        def make_click(side,index):
            def callback():self.click_item(side,index)
            return callback
        for side in ['Pack','Loot']:
            for i in range(30):
                button=self.widgets[f'{side}Item{i}'];button.set_editor_property('is_focusable',False)
                overlay=button.get_content();slot=overlay.get_editor_property('slot');slot.set_horizontal_alignment(u.HorizontalAlignment.H_ALIGN_FILL);slot.set_vertical_alignment(u.VerticalAlignment.V_ALIGN_FILL)
                text=self.widgets[f'{side}Text{i}'];text.set_auto_wrap_text(False);text.get_editor_property('slot').set_horizontal_alignment(u.HorizontalAlignment.H_ALIGN_FILL)
                icon=self.widgets[f'{side}Icon{i}'];icon.remove_from_parent();fit=u.new_object(u.ScaleBox,tree,f'{side}IconFit{i}');fit.set_stretch(u.Stretch.SCALE_TO_FIT);fit.add_child(icon);slot=overlay.add_child_to_overlay(fit);slot.set_horizontal_alignment(u.HorizontalAlignment.H_ALIGN_FILL);slot.set_vertical_alignment(u.VerticalAlignment.V_ALIGN_FILL);slot.set_padding(u.Margin(5,40,5,3));self.icon_fits.append(fit)
                callback=make_click(side,i)
                self.bindings.append(callback);button.on_clicked.add_callable(callback)
        self.bindings.append(self.take_all);self.widgets['TakeAll'].on_clicked.add_callable(self.take_all);self.widgets['TakeAll'].set_editor_property('is_focusable',False)
        caption=self.widgets['TakeAll'].get_content();font=caption.get_editor_property('font');font.set_editor_property('size',18);caption.set_font(font)
        self.equipment.build(tree)
    def open(self,target=None):
        self.ensure_widget();self.active=target;self.s.search=target;self.reveal=0.;self.feedback=''
        self.control(True)
        if not self.widget.call_method('IsInViewport'):self.widget.call_method('AddToViewport',args=(100,))
        self.draw()
    def close(self):
        self.equipment.cancel()
        if self.widget:self.widget.call_method('RemoveFromParent')
        self.active=None;self.s.search=None;self.reveal=0.;self.control(False)
    def say(self,text):self.feedback=text;self.feedback_until=self.s.clock+3.;self.draw()
    def click_item(self,side,index):
        if not self.s.inventory or self.s.clock<self.equipment.suppress_until:return
        source=self.s.pack if side=='Pack' else self.active['items'] if self.active else []
        if index>=len(source):return
        if side=='Pack':self.say('物品详情：'+source[index]['name']+'  %.2f kg'%source[index]['kg']);return
        entry=source[index]
        if not entry['known']:self.say('尚未搜索到这件物品');return
        if transfer(source,self.s.pack,entry):self.say('已转移：'+entry['name']);self.s.audio.play('Gear_Cloth',volume=.3)
        else:self.say('背包空间不足，物品仍在原处')
    def take_all(self):
        if not self.active:return
        count=0
        for entry in list(self.active['items']):
            if transfer(self.active['items'],self.s.pack,entry):count+=1
        self.say('已收取 %d 件；未发现或放不下的物品保留'%count)
    def draw(self):
        if not self.widget:return
        W=self.widgets;target=self.active
        W['RightTitle'].set_text(('尸体 / '+target['title'] if target.get('corpse') else '容器 / '+target['title']) if target else '未打开搜刮目标')
        W['RightSection'].set_text('随身装备与物资 / 6 × 5' if target and target.get('corpse') else '容器物资 / 6 × 5')
        unknown=sum(not i['known'] for i in target['items']) if target else 0
        W['SearchStatus'].set_text('检查中 · 剩余 %d 件未知物品'%unknown if unknown else '搜索完成' if target else '关闭背包，对准箱子或尸体按 F')
        W['SearchProgress'].set_percent(min(1,self.reveal/.85) if unknown else 1.)
        self.equipment.draw()
        W['Weight'].set_text('%.2f kg'%sum(i['kg'] for i in self.s.pack+list(filter(None,self.equipment.slots.values()))))
        W['Feedback'].set_text(self.feedback if self.s.clock<self.feedback_until else '拖拽物品 / 装备  ·  1 / 2 切枪  ·  Tab / Esc 关闭')
        colors={'MED':(.12,.20,.18,1),'AMMO':(.23,.20,.12,1),'WEAPON':(.21,.20,.15,1),'GEAR':(.14,.19,.13,1),'INTEL':(.13,.17,.22,1)}
        for side,entries,x in [('Pack',self.s.pack,48),('Loot',target['items'] if target else [],664)]:
            for i in range(30):
                b=W[f'{side}Item{i}'];t=W[f'{side}Text{i}']
                if i>=len(entries):b.set_visibility(u.SlateVisibility.COLLAPSED);continue
                entry=entries[i];known=entry.get('known',True);b.set_visibility(u.SlateVisibility.VISIBLE)
                slot=b.get_editor_property('slot');slot.set_position(u.Vector2D(x+86*entry['x'],282+62*entry['y']));slot.set_size(u.Vector2D(entry['w']*86-2,entry['h']*62-2))
                b.set_background_color(u.LinearColor(*(colors.get(entry['kind'],(.17,.18,.14,1)) if known else (.045,.047,.043,1))))
                short={'MK18 风格步枪':'MK18','FAST 风格头盔':'FAST','STANAG 弹匣':'STANAG','5.56 弹药':'5.56'}.get(entry['name'],entry['name'])
                t.set_text('%s\n%.2fkg'%(short,entry['kg']) if known else '?')
                from item_icons import texture as item_texture
                icon=W[f'{side}Icon{i}'];texture=item_texture(entry) if known else None
                icon.set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE if texture else u.SlateVisibility.COLLAPSED)
                if texture:icon.set_brush_from_texture(texture,True)
                b.set_tool_tip_text(entry['name']+'  点击转移' if known and side=='Loot' else '等待搜索' if not known else entry['name'])
    def target(self):
        eye=self.s.camera.get_world_location();forward=self.s.camera.get_forward_vector();best=None;limit=220.
        for box in self.s.boxes+self.corpses:
            actor=box['actor']
            if not valid(actor):continue
            pos=actor.get_actor_location()
            if box.get('corpse'):pos=actor.skeletal_mesh_component.get_socket_location('pelvis')+u.Vector(0,0,12)
            delta=pos-eye;dist=delta.length()
            if dist>limit or dist<.001 or (delta.x*forward.x+delta.y*forward.y+delta.z*forward.z)/dist<.78:continue
            hit=self.s.trace(eye,pos)
            if hit and self.s.hit_actor(hit)!=actor and distance(self.s.hit_point(hit),pos)>70:continue
            best=box;limit=dist
        return best
    def spawn_corpse(self,entry,index):
        entry['corpse_created']=True;npc=entry['actor'];api=u.get_default_object(u.GameplayStatics);tf=u.Transform()
        a=api.call_method('BeginDeferredActorSpawnFromClass',args=(self.s.world,u.SkeletalMeshActor.static_class(),tf,u.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
        a=api.call_method('FinishSpawningActor',args=(a,tf,u.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));a.set_actor_label('PMC corpse %02d'%(index+1));a.tags=[u.Name('SearchableCorpse')]
        c=a.skeletal_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_skeletal_mesh_asset(entry['body_mesh'])
        if valid(npc):
            a.set_actor_transform(npc.mesh.get_world_transform(),False,True)
            for i in range(npc.mesh.get_num_materials()):c.set_material(i,u.load_asset('/Game/Factory/Visual4/Materials/'+('M_PMC_Uniform' if i==0 else 'M_PMC_Black')))
        else:
            a.set_actor_location(entry['last_location']-u.Vector(0,0,90),False,True);a.set_actor_rotation(u.Rotator(yaw=entry['last_rotation'].yaw-90),False)
        death=u.load_asset('/Game/Characters/Mannequins/Anims/Death/MM_Death_Front_01')
        c.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE)
        if death:c.play_animation(death,False);c.set_position(.65,False)
        c.set_collision_profile_name('Ragdoll');a.set_life_span(0)
        # Reparent the already dressed equipment to the same bones on the corpse.
        for j,(owner,gear) in enumerate(list(self.s.pmc.parts)):
            if owner==npc and valid(gear):
                socket=gear.get_attach_parent_socket_name();gear.attach_to_component(c,socket,u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,u.AttachmentRule.KEEP_RELATIVE,False);self.s.pmc.parts[j]=(a,gear)
        weapon=self.s.prop(npc,'Weapon') if valid(npc) else None
        if valid(weapon):weapon.call_method('Stop Firing');weapon.destroy_actor()
        if valid(npc):npc.destroy_actor()
        self.pending_physics.append((self.s.clock+.15,a))
        corpse={'actor':a,'title':'PMC %02d'%(index+1),'corpse':True,'items':contents(corpse=True),'searched':False}
        self.corpses.append(corpse)
        if not entry['dead']:entry['dead']=True;self.s.kills+=1
        return corpse
    def deaths(self):
        for index,entry in enumerate(self.s.enemies):
            npc=entry['actor']
            if entry['corpse_created']:continue
            if valid(npc):
                entry['last_location']=npc.get_actor_location();entry['last_rotation']=npc.get_actor_rotation()
            if not valid(npc) or npc.actor_has_tag('Dead') or self.s.prop(npc,'Current HP',1)<=0:self.spawn_corpse(entry,index)
        for when,a in list(self.pending_physics):
            if self.s.clock>=when:
                if valid(a):a.skeletal_mesh_component.set_simulate_physics(True)
                self.pending_physics.remove((when,a))
    def update(self,dt,keys):
        self.equipment.update(keys)
        self.deaths();self.s.focus=self.target()
        pressed=lambda k:k in keys and k not in self.s.previous
        if pressed('Escape') and self.s.inventory:self.close();return
        if pressed('Tab'):
            if self.s.inventory:self.close()
            else:self.open()
            return
        if not self.s.inventory and pressed('F') and self.s.focus:self.open(self.s.focus)
        if not self.s.inventory:return
        if self.active:
            actor=self.active['actor']
            if not valid(actor) or distance(self.s.player.get_actor_location(),actor.skeletal_mesh_component.get_socket_location('pelvis') if self.active.get('corpse') else actor.get_actor_location())>320:
                self.close();self.s.say('已远离搜刮目标');return
            unknown=next((i for i in self.active['items'] if not i['known']),None)
            if unknown:
                self.reveal+=dt
                if self.reveal>=.85:unknown['known']=True;self.reveal=0.;self.s.audio.play('Search_Latch',volume=.22)
            else:self.active['searched']=True
        if self.s.clock-self.last_draw>.1:self.last_draw=self.s.clock;self.draw()
