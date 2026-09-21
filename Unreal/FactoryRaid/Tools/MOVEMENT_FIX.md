# WASD 异常走位修复

问题并非标准 WASD 正负轴设置错误。运行时检查发现 Specter 镜片与 XPS3 组件变为 `BlockAll / QueryAndPhysics`；隐藏的瞄具依然发生实体碰撞，导致角色被挤向后侧，甚至抵消前进输入。

`scope_optic.py` 在创建完整瞄具后将各部件设为持久 `NoCollision` 碰撞配置，同时在 Actor 层禁用碰撞。切换武器时再次保持 Actor 碰撞禁用。保留原来的 Enhanced Input 映射及角色移动系统；排查中临时添加的键盘接管代码已撤回。

验证脚本 `test_movement.py` 在 PIE 隔离平台上使用现有按键的真实 InputAction、Modifier、Trigger，通过 Enhanced Input 注入输入并测量角色物理位移。这是自动化引擎输入测试，不是真实硬件键盘操作记录。

覆盖 HK416 腰射、MK18 开镜，四个朝向，每个朝向 W/A/S/D 与静止，共40项；同时检查所有瞄具组件未恢复实体碰撞。结果见 `movement_test.json`。修复前数据见 `movement_before.json`（早期平台搭建也有缺陷，因此不把修复前位移值当作严格同条件性能对比）。

关闭旧试玩窗口并重新运行原来的启动脚本，让新 Python 控制器生效。
