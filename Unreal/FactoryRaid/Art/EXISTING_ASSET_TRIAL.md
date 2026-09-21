# 现成高清素材试装（2026-09-09）

本轮实际导入 3 组 Poly Haven CC0 模型至 `/Game/Realism/PolyHaven`，布置在破冰船机舱入口维修区。保留现有场景和玩法，原地图备份 `Tools/PolyHavenBackup/Icebreaker.umap`。根目录 `试用高清素材.cmd` 直接出生在试装位置。

来源：[Poly Haven 许可](https://polyhaven.com/license)。保存逐文件 URL、MD5 和作者信息于 `Tools/PolyHavenSource/manifest.json`。下载脚本校验了全部 19 个文件。

## Portable Generator

来源：[portable_generator](https://polyhaven.com/a/portable_generator)；作者：James Ray Cock。

1. **真实尺寸**：UE 导入包围盒 81.83×56.40×57.69 cm；原始 FBX 单位转换后保持 scale=1。以作者模型为依据，中等可信度，未对实物测量；木箱是源文件整个组合包围盒，不冒称单个箱子的产品尺寸。
2. **建模拆分**：保留源文件网格组合与 UV；发电机机体、管架、线路等均为现成模型，工具柜按静态道具导入，木箱保留源组合。当前不提供抽屉/箱盖交互动画。
3. **高模重点**：本项目未制作或重新烘焙高模；保留作者正常形体、边缘倒角和烘焙法线。高模工程未导入，无法核验烘焙流程。
4. **低模重点**：作者 API polycount=26419（不能等同于 UE 实测 tris）；保留源拓扑。目标本次 3 组总计不超过 120k tris，UE 三角形统计尚未完成。
5. **UV**：沿用作者唯一 UV 和原 PBR 配套贴图，无新增平铺划痕，不修改标识 UV。Lightmap 使用导入生成方案，当前主要依赖动态照明。
6. **Texel Density**：近距离环境道具目标 10–20 px/cm；实际 UV 局部密度未测量，4K 不等于所有区域达到该密度。以正常第一人称距离验收。
7. **材质层级**：原始 BaseColor、Metallic、Roughness、Normal、AO；保留作者的涂层、裸金属、橡胶/木材分区及已有接触磨损，不额外随机叠污迹。
8. **Roughness**：源图像素范围 1.000–1.000；材质直接采样，不把整件强制设为金属。建议涂层约 .4–.8、橡胶 .7–.95，数值属校准参考而非实物测量。
9. **贴图分辨率**：Diffuse: 4096×4096；nor_dx: 4096×4096；Rough: 4096×4096；Metal: 4096×4096；AO: 4096×4096；Alpha: 4096×4096。BaseColor sRGB；其余线性；DX 法线使用 Normalmap 压缩。未下载 Height，不制造假位移。
10. **LOD / Nanite**：保留导入静态网格，本轮未开启 Nanite、未生成新 LOD。现仅各放一组，后续铺全图前需 LOD 和实例化规划。
11. **UE 材质**：Default Lit，原 UV 采样；发电机 Alpha 使用 Masked，其他 Opaque。法线 sampler=Normal，数据图 sampler=Masks；Mip 与默认纹理过滤开启。
12. **碰撞**：FBX 自动生成简单碰撞，场景 Actor 使用 BlockAll。摆放在中央通道两侧；具体凸包贴合度与各方向绕行仍需人工试玩。没有改动玩家或枪械碰撞。
13. **性能预算**：材质槽 2，全分辨率压缩贴图目标每组 ≤128 MiB；不是实测驻留内存。未做 GPU 帧耗时测量，暂不大量复制。
14. **真实性检查**：来源/许可 PASS；尺寸导入 PASS；配套 PBR/颜色空间 PASS；未新增随机磨损 PASS；实际第一人称截图见 `Tools/polyhaven_service.png` 与 `polyhaven_crate.png`；人物、手臂和大环境仍为旧资产，不标记 AAA 达标。

## Metal Tool Chest

来源：[metal_tool_chest](https://polyhaven.com/a/metal_tool_chest)；作者：Yann Kervran、John Hutcheson。

1. **真实尺寸**：UE 导入包围盒 68.54×40.72×65.18 cm；原始 FBX 单位转换后保持 scale=1。以作者模型为依据，中等可信度，未对实物测量；木箱是源文件整个组合包围盒，不冒称单个箱子的产品尺寸。
2. **建模拆分**：保留源文件网格组合与 UV；发电机机体、管架、线路等均为现成模型，工具柜按静态道具导入，木箱保留源组合。当前不提供抽屉/箱盖交互动画。
3. **高模重点**：本项目未制作或重新烘焙高模；保留作者正常形体、边缘倒角和烘焙法线。高模工程未导入，无法核验烘焙流程。
4. **低模重点**：作者 API polycount=14576（不能等同于 UE 实测 tris）；保留源拓扑。目标本次 3 组总计不超过 120k tris，UE 三角形统计尚未完成。
5. **UV**：沿用作者唯一 UV 和原 PBR 配套贴图，无新增平铺划痕，不修改标识 UV。Lightmap 使用导入生成方案，当前主要依赖动态照明。
6. **Texel Density**：近距离环境道具目标 10–20 px/cm；实际 UV 局部密度未测量，4K 不等于所有区域达到该密度。以正常第一人称距离验收。
7. **材质层级**：原始 BaseColor、Metallic、Roughness、Normal、AO；保留作者的涂层、裸金属、橡胶/木材分区及已有接触磨损，不额外随机叠污迹。
8. **Roughness**：源图像素范围 1.000–1.000；材质直接采样，不把整件强制设为金属。建议涂层约 .4–.8、橡胶 .7–.95，数值属校准参考而非实物测量。
9. **贴图分辨率**：Diffuse: 4096×4096；nor_dx: 4096×4096；Rough: 4096×4096；Metal: 4096×4096；AO: 4096×4096。BaseColor sRGB；其余线性；DX 法线使用 Normalmap 压缩。未下载 Height，不制造假位移。
10. **LOD / Nanite**：保留导入静态网格，本轮未开启 Nanite、未生成新 LOD。现仅各放一组，后续铺全图前需 LOD 和实例化规划。
11. **UE 材质**：Default Lit，原 UV 采样；发电机 Alpha 使用 Masked，其他 Opaque。法线 sampler=Normal，数据图 sampler=Masks；Mip 与默认纹理过滤开启。
12. **碰撞**：FBX 自动生成简单碰撞，场景 Actor 使用 BlockAll。摆放在中央通道两侧；具体凸包贴合度与各方向绕行仍需人工试玩。没有改动玩家或枪械碰撞。
13. **性能预算**：材质槽 1，全分辨率压缩贴图目标每组 ≤128 MiB；不是实测驻留内存。未做 GPU 帧耗时测量，暂不大量复制。
14. **真实性检查**：来源/许可 PASS；尺寸导入 PASS；配套 PBR/颜色空间 PASS；未新增随机磨损 PASS；实际第一人称截图见 `Tools/polyhaven_service.png` 与 `polyhaven_crate.png`；人物、手臂和大环境仍为旧资产，不标记 AAA 达标。

## Old Military Crate

来源：[old_military_crate](https://polyhaven.com/a/old_military_crate)；作者：Jack Mava。

1. **真实尺寸**：UE 导入包围盒 181.54×97.57×30.09 cm；原始 FBX 单位转换后保持 scale=1。以作者模型为依据，中等可信度，未对实物测量；木箱是源文件整个组合包围盒，不冒称单个箱子的产品尺寸。
2. **建模拆分**：保留源文件网格组合与 UV；发电机机体、管架、线路等均为现成模型，工具柜按静态道具导入，木箱保留源组合。当前不提供抽屉/箱盖交互动画。
3. **高模重点**：本项目未制作或重新烘焙高模；保留作者正常形体、边缘倒角和烘焙法线。高模工程未导入，无法核验烘焙流程。
4. **低模重点**：作者 API polycount=10476（不能等同于 UE 实测 tris）；保留源拓扑。目标本次 3 组总计不超过 120k tris，UE 三角形统计尚未完成。
5. **UV**：沿用作者唯一 UV 和原 PBR 配套贴图，无新增平铺划痕，不修改标识 UV。Lightmap 使用导入生成方案，当前主要依赖动态照明。
6. **Texel Density**：近距离环境道具目标 10–20 px/cm；实际 UV 局部密度未测量，4K 不等于所有区域达到该密度。以正常第一人称距离验收。
7. **材质层级**：原始 BaseColor、Metallic、Roughness、Normal、AO；保留作者的涂层、裸金属、橡胶/木材分区及已有接触磨损，不额外随机叠污迹。
8. **Roughness**：源图像素范围 1.000–1.000；材质直接采样，不把整件强制设为金属。建议涂层约 .4–.8、橡胶 .7–.95，数值属校准参考而非实物测量。
9. **贴图分辨率**：Diffuse: 4096×4096；nor_dx: 4096×4096；Rough: 4096×4096；Metal: 4096×4096；AO: 4096×4096。BaseColor sRGB；其余线性；DX 法线使用 Normalmap 压缩。未下载 Height，不制造假位移。
10. **LOD / Nanite**：保留导入静态网格，本轮未开启 Nanite、未生成新 LOD。现仅各放一组，后续铺全图前需 LOD 和实例化规划。
11. **UE 材质**：Default Lit，原 UV 采样；发电机 Alpha 使用 Masked，其他 Opaque。法线 sampler=Normal，数据图 sampler=Masks；Mip 与默认纹理过滤开启。
12. **碰撞**：FBX 自动生成简单碰撞，场景 Actor 使用 BlockAll。摆放在中央通道两侧；具体凸包贴合度与各方向绕行仍需人工试玩。没有改动玩家或枪械碰撞。
13. **性能预算**：材质槽 1，全分辨率压缩贴图目标每组 ≤128 MiB；不是实测驻留内存。未做 GPU 帧耗时测量，暂不大量复制。
14. **真实性检查**：来源/许可 PASS；尺寸导入 PASS；配套 PBR/颜色空间 PASS；未新增随机磨损 PASS；实际第一人称截图见 `Tools/polyhaven_service.png` 与 `polyhaven_crate.png`；人物、手臂和大环境仍为旧资产，不标记 AAA 达标。

## 其他可继续使用的库

- [ambientCG](https://ambientcg.com/)：CC0 PBR 表面库，适合混凝土、油漆、布料、锈蚀。此次未额外下载。
- [Quantum 免费军事人物样本](https://www.fab.com/listings/8e200050-3158-4762-b297-f785b5b1533d)：Fab 标准许可；页面标明 UE5 骨架、支持 UE5.0–5.8，包含 FBX 与 PBR 纹理包。网页报告下载完成，但本地项目尚未取得可导入文件，本轮敌人没有替换。
- [Quantum Modular Military Character](https://www.fab.com/listings/d39bebbc-2e92-4ef9-a5b1-831e04f6a51c)：收费完整人物库候选；未购买。

Fab 标准许可与 CC0 不同，允许集成到项目，但不能将素材单独再分发。参考 https://www.fab.com/eula 。

## 实测与尚未通过的项目

- DX12 PIE 运行成功；3 组新模型已出现在现有地图，6 个敌人、6 个原搜刮点数量断言通过。本轮新木箱、工具柜是环境道具，还没有绑定新的搜刮点。
- 第一人称目视：发电机机架、发动机附件、工具柜抽屉及箱体结构/作者贴图可辨认；不是增加随机噪点的程序方块。
- FAIL：维修区直射光下旧枪械明显发白，大型船用发电机和墙面仍然简化，尚未达到整景写实目标。
- 日志存在既有 `LogUtils: The Editor is currently in a play mode` 和启动自动化 Condition failed 记录；不能宣称整个项目日志无错误。本次导入没有 Python 异常或 Failed to compile Material 记录。
- 对比截图：`Tools/polyhaven_before.png` 在 PIE 暂时隐藏新增道具，`Tools/polyhaven_service.png` 显示相同位置的道具；关卡保存内容始终包含新道具。图片是实际 UE 渲染，没有后期美化。
