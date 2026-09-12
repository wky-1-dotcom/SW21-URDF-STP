# `urdf_sw_description`（ROS 2 Foxy 旧版）

本目录是仓库中旧 Foxy/RViz2 description 包的另一份历史副本，和 `ROS2/RViz2/urdf_sw_description/` 用途相同。它只用于 SolidWorks URDF 的显示和 TF 检查，不是 Humble 仿真包。

旧版坐标系为：

```text
base_link -> b0 -> l1 -> l2 -> l3 -> l4 -> l5 -> l6
                                             └─ gripper_slider_joint -> gripper_link
```

`base_link` 是虚拟根，`b0` 是实体底座；`l6` 是六轴机械臂末端；`gripper_link` 是导出后的末端可视化 link，不代表已经具备真实夹爪开合控制。没有末端工具时使用 `l6` 作为末端；需要工具时增加 `tool0`/`tcp` fixed frame，并写清相对位姿。

通用转换模板见 [`docs/ROS2_Foxy_URDF_通用转换模板.md`](../../docs/ROS2_Foxy_URDF_通用转换模板.md)。当前 Humble 主线见 [`ROS2/Humble/README.md`](../../ROS2/Humble/README.md)。
