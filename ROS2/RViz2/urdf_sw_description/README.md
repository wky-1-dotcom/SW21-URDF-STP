# urdf_sw_description（ROS 2 Foxy / RViz2）

这是旧版 Foxy/RViz2 description 包，用于验证 SolidWorks 导出的六轴机械臂模型、STL 路径、TF 和关节显示。它不包含 Gazebo、`ros2_control`、MoveIt 2 或真实硬件驱动。

## 坐标系和末端

```text
base_link                         虚拟根坐标系
└── base_link_to_b0 [fixed]
    └── b0 -> l1 -> l2 -> l3 -> l4 -> l5 -> l6
        └── gripper_slider_joint [prismatic]
            └── gripper_link
```

`base_link` 是统一 TF 根，`b0` 是实体底座。当前 Foxy 包没有真实的二指夹爪开合机构；`gripper_link` 是末端可视化 link，`gripper_slider_joint` 是导出后整理的显示用直线关节。如果没有末端工具，可以把 `l6` 作为末端；如果需要工具坐标系，使用 fixed joint 添加 `tool0` 和 `tcp`，并记录真实的 xyz/rpy。

通用转换步骤见仓库中的 [`docs/ROS2_Foxy_URDF_通用转换模板.md`](../../../docs/ROS2_Foxy_URDF_通用转换模板.md)。

## 放入 Foxy 工作空间

```bash
source /opt/ros/foxy/setup.bash
mkdir -p ~/foxy_ws/src
cp -a ROS2/RViz2/urdf_sw_description ~/foxy_ws/src/
cd ~/foxy_ws
colcon build --symlink-install --packages-select urdf_sw_description
source install/setup.bash
ros2 launch urdf_sw_description display.launch.py
```

RViz2 中将 `Fixed Frame` 设置为 `base_link`，确认 `RobotModel` 为 `Ok`。拖动 `j1` 到 `j6` 和末端显示关节，检查旋转轴、零位和行程是否符合 SolidWorks 装配体。

## 说明

- `package://urdf_sw_description/meshes/...` 的包名必须与 `package.xml` 一致；
- Linux 区分 `.STL` 和 `.stl` 的大小写；
- 显示测试限位、质量和惯量不能直接用于仿真或实机；
- 需要 Gazebo/MoveIt 2 时，使用仓库中的 `ROS2/Humble/` 主线，不要把两个包混在同一工作空间中。
