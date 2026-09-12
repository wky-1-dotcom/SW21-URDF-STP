# `cr7as_grasp` 的 ROS 2 Humble 转换与故障排查

本文记录本包从 SolidWorks SW2URDF 导出物转换到 ROS 2 Humble + Gazebo Classic 的项目特例。通用方法请先看仓库中的 [`docs/ROS2_Humble_URDF_通用转换模板.md`](../../../../docs/ROS2_Humble_URDF_通用转换模板.md)。

## 原始包到当前包的主要变化

| 项目 | SW2URDF/ROS 1 原始输出 | 当前 Humble 包 |
| --- | --- | --- |
| 构建系统 | `catkin` | `ament_cmake` |
| 启动文件 | ROS 1 XML launch | Python launch |
| 可视化 | `rviz` | `rviz2` |
| Gazebo 生成 | `spawn_model -file` | `spawn_entity.py -topic robot_description` |
| 控制接口 | 无 `ros2_control` | `gazebo_ros2_control` + controller YAML |
| 根坐标系 | 通常从 `b0` 开始 | `base_link -> b0` |
| 末端 | 原导出夹爪/工具结构不可靠 | `gripper_base` 固定，`grasp_tcp` 为无几何 TCP |

## 当前坐标系

```text
base_link
└── base_link_to_b0 [fixed]
    └── b0 -> l1 -> l2 -> l3 -> l4 -> l5 -> l6
        └── gripper_base_j [fixed]
            └── gripper_base
                └── grasp_tcp_j [fixed]
                    └── grasp_tcp
```

`base_link` 是统一 TF 根，`b0` 是实体底座；`gripper_base` 是固定末端 CAD 模型；`grasp_tcp` 是规划工具坐标系，不是夹爪开合 link。当前模型没有夹爪指爪、丝杠或开合控制。

## 典型错误和处理顺序

### 1. Gazebo 找不到网格

检查 URDF 是否使用：

```xml
package://cr7as_grasp/meshes/l1.STL
```

并确认 `CMakeLists.txt` 安装了 `meshes`。Linux 区分大小写，`l1.STL` 和 `l1.stl` 不是同一个文件。

### 2. Gazebo 找不到控制器 YAML

`gazebo_control.launch.py` 会读取安装后的：

```text
cr7as_grasp/config/gazebo_controllers.yaml
```

如果修改了包名或目录，必须同步修改 `package.xml`、`CMakeLists.txt`、URDF 的 `package://` 和 launch 中的包名。

### 3. `/controller_manager` 不存在

按以下顺序检查：

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 node list
ros2 topic echo /clock --once
ros2 control list_controllers -c /controller_manager
```

如果 Gazebo 没有启动，或者 URDF 中没有正确加载 `gazebo_ros2_control/GazeboSystem`，控制器不会出现。先修复 Gazebo 生成和插件加载，再启动 spawner。

### 4. MoveIt 规划时钟不一致

Gazebo 发布 `/clock` 时，MoveIt、RViz 和 Robot State Publisher 应使用仿真时间：

```bash
ros2 param get /move_group use_sim_time
ros2 node list
```

当前 MoveIt launch 已设置 `use_sim_time=True`。不要把旧 Foxy 的 FakeSystem MoveIt 配置和 Gazebo 控制链同时启动。

### 5. 源文件已经改了但运行结果没变

Humble 工作空间需要重新构建并重新 source：

```bash
cd <仓库路径>/ROS2/Humble
colcon build --symlink-install --packages-select cr7as_grasp cr7as_grasp_moveit_config
source install/setup.bash
```

确认正在运行的包来自当前工作空间：

```bash
ros2 pkg prefix cr7as_grasp
ros2 pkg prefix cr7as_grasp_moveit_config
```

## 仍需实测的内容

- `grasp_tcp` 相对夹爪实际中心的 xyz/rpy；
- 夹爪真实质量、质心和惯量；
- 简化 collision mesh；
- 夹爪开合关节、丝杠导程和控制接口；
- 真实厂家关节限位、速度、力矩和安全参数。

当前文件可以用于 Humble 仿真和规划验证，但不能据此直接驱动真实机械臂。
