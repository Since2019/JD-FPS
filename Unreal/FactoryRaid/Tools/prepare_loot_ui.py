"""Author a native UMG overlay using the public panel/slot APIs."""
import unreal as u,os,json
A=u.AssetToolsHelpers.get_asset_tools();P='/Game/Factory/Visual4/UI/WBP_Loot_v2'
bp=u.load_asset(P) or u.EditorAssetLibrary.duplicate_asset('/Game/Variant_Shooter/UI/UI_Shooter',P)
tree=u.find_object(bp,'WidgetTree');assert tree
root=u.find_object(tree,'Overlay_26');assert isinstance(root,u.Overlay)
# Keep the template's bound score widgets valid but invisible. Only this duplicate
# receives the new UI; the template crosshair class remains independently hidden.
for child in root.get_all_children():child.set_visibility(u.SlateVisibility.COLLAPSED)
def new(cls,name):return u.find_object(tree,name) or u.new_object(cls,tree,name)
scale=new(u.ScaleBox,'LootScale');slot=root.add_child_to_overlay(scale);slot.set_horizontal_alignment(u.HorizontalAlignment.H_ALIGN_FILL);slot.set_vertical_alignment(u.VerticalAlignment.V_ALIGN_FILL);scale.set_stretch(u.Stretch.SCALE_TO_FIT)
scale.set_visibility(u.SlateVisibility.VISIBLE)
size=new(u.SizeBox,'LootSize');size.set_width_override(1280);size.set_height_override(720);scale.add_child(size)
canvas=new(u.CanvasPanel,'LootCanvas');size.add_child(canvas);canvas.clear_children()
def place(w,x,y,width,height):
    slot=canvas.add_child_to_canvas(w);slot.set_position(u.Vector2D(x,y));slot.set_size(u.Vector2D(width,height));return w
def panel(name,x,y,w,h,color):
    p=new(u.Border,name);p.set_brush_color(u.LinearColor(*color));place(p,x,y,w,h);return p
def label(name,text,x,y,w,h=30,size=18,color=(.78,.79,.74,1)):
    t=new(u.TextBlock,name);t.set_text(text);font=t.get_editor_property('font');font.set_editor_property('size',size);t.set_font(font);t.set_color_and_opacity(u.SlateColor(specified_color=u.LinearColor(*color)));place(t,x,y,w,h);t.set_visibility(u.SlateVisibility.HIT_TEST_INVISIBLE);return t
panel('Backdrop',0,0,1280,720,(.009,.012,.012,.95))
panel('TopBar',26,24,1228,55,(.027,.033,.032,1))
label('Brand','RAID  /  装备与搜刮',46,37,620,35,24)
label('CloseHint','TAB / ESC 关闭',1020,44,220,25,16)
panel('LeftPanel',26,94,597,560,(.023,.028,.027,.98));panel('RightPanel',640,94,614,560,(.018,.023,.022,.98))
label('LeftTitle','你的装备',48,110,460,35,24)
label('RightTitle','搜索容器',664,110,560,35,24)
label('LeftInfo','背包  /  6 × 5',48,240,480,30,17)
label('SearchStatus','等待搜索',664,153,550,30,16,(.62,.64,.52,1))
label('Weight','0.0 kg',460,240,150,25,16)
label('RightSection','容器物资  /  6 × 5',664,240,530,25,17)
for name,x,w,txt in [('HeadSlot',48,158,'头部\nFAST 风格头盔'),('VestSlot',218,158,'护具\n战术携行背心'),('WeaponSlot',388,211,'主武器\nMK18 风格步枪')]:
    panel(name,x,154,w,66,(.05,.056,.05,1));label(name+'Text',txt,x+10,165,w-16,58,16)
for side,x in [('Pack',48),('Loot',664)]:
    for y in range(5):
        for col in range(6):panel('%sGrid%d_%d'%(side,col,y),x+col*86,282+y*62,84,60,(.042,.048,.044,1))
    for i in range(30):
        b=new(u.Button,'%sItem%d'%(side,i));b.set_is_enabled(True);b.set_background_color(u.LinearColor(.17,.19,.14,1));place(b,x,282,84,60)
        overlay=new(u.Overlay,'%sOverlay%d'%(side,i));b.add_child(overlay)
        img=new(u.Image,'%sIcon%d'%(side,i));slot=overlay.add_child_to_overlay(img);slot.set_horizontal_alignment(u.HorizontalAlignment.H_ALIGN_FILL);slot.set_vertical_alignment(u.VerticalAlignment.V_ALIGN_FILL);slot.set_padding(u.Margin(4,16,4,14))
        t=new(u.TextBlock,'%sText%d'%(side,i));slot=overlay.add_child_to_overlay(t);slot.set_vertical_alignment(u.VerticalAlignment.V_ALIGN_TOP);f=t.get_editor_property('font');f.set_editor_property('size',13);t.set_font(f);t.set_color_and_opacity(u.SlateColor(specified_color=u.LinearColor(.87,.86,.76,1)));t.set_auto_wrap_text(True);b.set_visibility(u.SlateVisibility.COLLAPSED)
label('Feedback','点击右侧物品转移；背包满时物资保留。',48,670,970,28,17)
button=new(u.Button,'TakeAll');place(button,1025,665,228,36);text=new(u.TextBlock,'TakeAllText');text.set_text('收取已发现物品');button.add_child(text)
progress=new(u.ProgressBar,'SearchProgress');place(progress,664,191,560,7);progress.set_fill_color_and_opacity(u.LinearColor(.47,.51,.32,1))
for name in ['Weapon','Helmet']:
    task=u.AssetImportTask();task.filename=os.path.join(os.path.dirname(__file__),'Visual4Source','Icon_'+name+'.png');task.destination_path='/Game/Factory/Visual4/UI';task.destination_name='Icon_'+name;task.automated=True;task.save=True;task.replace_existing=True;A.import_asset_tasks([task])
    tex=u.load_asset('/Game/Factory/Visual4/UI/Icon_'+name);tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON);tex.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_UI);u.EditorAssetLibrary.save_loaded_asset(tex)
u.BlueprintEditorLibrary.compile_blueprint(bp);assert u.EditorAssetLibrary.save_loaded_asset(bp)
open(os.path.join(os.path.dirname(__file__),'loot_ui_prepare.json'),'w').write(json.dumps({'ready':True,'path':P}))
u.log('LOOT_UI_READY')
