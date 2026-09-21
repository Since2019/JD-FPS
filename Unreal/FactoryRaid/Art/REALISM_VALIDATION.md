# 本轮验收：写实基础整改，不是 AAA 成品验收

测试环境：Windows、AMD Radeon RX 7900 XTX、UE 5.8、D3D12 / SM6。游戏运行仍为 Editor PIE + Python。截图 1280×720，未用图片处理伪造游戏效果。

## 通过项

- 工厂与破冰船均正常进入 PIE、自动瞄准及射击。
- 工厂保留6名敌人、8个搜索对象；破冰船6名敌人、6个搜索对象。
- 两张图最终运行日志没有 `Failed to compile Material` 或 Python 错误。
- 全息镜实际外廓：9.6500×5.3300×6.3500 cm；ADS 轴线误差小于 .001 cm。此数值只说明轴线对齐，不证明完整人体工学。
- 运行时 GI=1、Reflection=1、VirtualShadow=1，日志确认 D3D12 SM6；未以DX11截图冒充新渲染路径。没有宣称所有资产已启用Nanite。
- 动态手臂材质保留原头部隐藏遮罩，最终画面不再被身体挡住。中途失败的整体材质替换已撤回。
- 现有网格库存的8个单元测试通过；本轮并未重新做真实鼠标拖拽测试。
- 27个基础表面重新区分粗糙度和金属度，去掉满铺随机磨损；保留扫描材质，修正导入数据图色彩空间与采样器。
- 灯光/地图/材质原文件保存在 `../Tools/RealismBackup/`，后续重复应用不会覆盖首次备份。

## 视觉检查仍未达标

- 船体、设备、家具与人物仍有明显基本体/模板外形；尚不是可信的实船或真人装备重建。
- 第一人称袖子仍是模板硬表面轮廓，手与枪的贴合、手套法线和专属换弹动画仍需重做。
- 镜窗开口与厂家尺寸仍不完全一致；当前只完成外廓校准。
- 工厂大面材质重复、机舱顶面高光和船桥窗口亮度仍需更细的局部曝光/照明设计；本轮不能将“高光完全不溢出”标为通过。
- 裸露五金与涂层需要独立材质ID蒙版，目前同组涂层处理只是修正整片导体反射的过渡方案。
- 两处油迹有维护位置依据，但尚未单独做近景投影穿透与视觉验收。
- 专业高低模烘焙、密度统一、完整LOD、Nanite逐资产筛选、GPU profile、60fps指标均未完成。
- 鞋印、电缆、胶带、维修标签、生活用品等环境叙事资产没有在本轮批量生成；不要据规范文本宣称它们已经存在。

## 证据

- `../Tools/realism_factory_test.json`、`../Tools/realism_icebreaker_test.json`
- `../Tools/realism_factory_final.log`、`../Tools/realism_icebreaker_final.log`
- `../Tools/realism_factory_hip.png`、`realism_factory_ads.png`
- `../Tools/realism_icebreaker_hip.png`、`realism_icebreaker_ads.png`、`realism_icebreaker_engine.png`、`realism_icebreaker_bridge.png`

最终发布质量判定：**尚未达到用户要求的塔科夫级写实质量**。本轮完成规范固化和可验证的基础整改，后续应优先重制近景人物/手臂、设备轮廓和场景构件，不能继续依赖随机贴图掩盖结构不足。
