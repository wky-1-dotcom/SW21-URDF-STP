# CR7AS ROS 2 Humble 仿真工作空间

本目录是适配 Ubuntu 22.04 + ROS 2 Humble 的当前 CR7AS 主线。它只包含两个已验证的 ROS 2 包：

```text
ROS2/Humble/
├── README.md
└── src/
    ├── cr7as_grasp/
    └── cr7as_grasp_moveit_config/
```

## 功能包和坐标系

`cr7as_grasp` 提供 URDF、STL、Gazebo Classic 和 `ros2_control`；`cr7as_grasp_moveit_config` 提供 MoveIt 2 的 SRDF、运动学、关节限制、控制器映射和 RViz 配置。

当前 CR7AS 拓扑：

```text
base_link                         URDF 虚拟根，不是实体
└── base_link_to_b0 [fixed]
    └── b0                         机器人实体底座
        └── j1 -> l1
            └── j2 -> l2
                └── j3 -> l3
                    └── j4 -> l4
                        └── j5 -> l5
                            └── j6 -> l6
                                └── gripper_base_j [fixed]
                                    └── gripper_base  固定末端模型
                                        └── grasp_tcp_j [fixed]
                                            └── grasp_tcp  工具/TCP坐标系
```

MoveIt SRDF 中的 `world` 是 virtual joint 的父坐标系，不是 URDF 中的实体 link。`gripper_base` 当前固定在 `l6` 上，没有夹爪开合关节；`grasp_tcp` 是规划和工具中心点坐标系，没有 visual/collision。

通用转换原则见仓库根目录的 [`docs/ROS2_Humble_URDF_通用转换模板.md`](../../docs/ROS2_Humble_URDF_通用转换模板.md)。

## 安装依赖

```bash
sudo apt update
sudo apt install \
  python3-colcon-common-extensions \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-joint-state-publisher-gui \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  ros-humble-moveit \
  ros-humble-moveit-setup-assistant
```

## 构建

在仓库根目录执行：

```bash
cd ROS2/Humble
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select \
  cr7as_grasp \
  cr7as_grasp_moveit_config
source install/setup.bash
```

不要把 `build/`、`install/` 或 `log/` 上传到 GitHub，它们是本地构建产生的目录。

## RViz2 模型预览

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch cr7as_grasp display.launch.py
```

## Gazebo Classic、MoveIt 2 和 RViz2

在每个终端加载环境：

```bash
source /opt/ros/humble/setup.bash
source <仓库路径>/ROS2/Humble/install/setup.bash
```

终端 1：

```bash
ros2 launch cr7as_grasp gazebo_control.launch.py
```

终端 2：

```bash
ros2 control list_controllers -c /controller_manager
```

预期至少看到：

```text
joint_state_broadcaster  active
arm_controller           active
```

终端 3：

```bash
ros2 launch cr7as_grasp_moveit_config move_group.launch.py
```

终端 4：

```bash
ros2 launch cr7as_grasp_moveit_config moveit_rviz.launch.py
```

Gazebo 发布 `/clock`，所以 MoveIt 和 RViz 配置为 `use_sim_time: true`。不要同时启动旧 Foxy 的 `urdf_ros2_moveit_config` FakeSystem 配置。

## 最小诊断

```bash
ros2 topic echo /clock --once
ros2 topic echo /joint_states --once
ros2 action info /arm_controller/follow_joint_trajectory
ros2 param get /move_group use_sim_time
ros2 node list
```

## 限制

- 当前末端工具固定安装，尚未建模夹爪指爪、丝杠、闭环联动或开合控制；
- 当前 collision 复用详细 STL，高频规划前应制作简化 collision mesh；
- 质量、惯量、关节限位、速度和 TCP 位置仍需使用厂家资料或实测数据校准；
- 本配置使用 Gazebo Classic，不是 Gazebo Sim / Ignition 插件配置；
- 公开仓库前必须确认 CAD、STEP、STL 和机器人数据的再分发许可。
