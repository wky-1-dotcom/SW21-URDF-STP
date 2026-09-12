# SolidWorks 导出的 URDF 转 ROS 2 Humble 通用模板

本文适用于从 SolidWorks SW2URDF 导出的 URDF/ROS 1 包，目标是 Ubuntu 22.04 + ROS 2 Humble。Humble 与 Foxy 使用同一套 URDF 基本元素；Humble 迁移的重点是 ROS 2 包、Python launch、依赖、仿真控制链和 MoveIt 2 配置，而不是重新发明 URDF XML。

## 1. 先确定目标层次

把项目拆成逐层可验证的包：

```text
description 包
  URDF + STL + RViz2 + joint_state_publisher_gui

Gazebo 包/配置
  Gazebo Classic 或 Gazebo Sim 插件 + ros2_control + controllers

MoveIt 2 配置包
  SRDF + kinematics + planning limits + controller mapping + RViz MotionPlanning

硬件包（可选）
  厂商驱动、通信、安全、真实控制器
```

不要因为系统升级到 Humble，就把 Gazebo、MoveIt 2 或真实硬件配置自动混进 description 包。每层先独立验证。

## 2. 推荐工作空间结构

```text
humble_ws/
├── src/
│   ├── YOUR_DESCRIPTION_PACKAGE/
│   │   ├── CMakeLists.txt
│   │   ├── package.xml
│   │   ├── launch/
│   │   ├── config/
│   │   ├── meshes/
│   │   ├── rviz/
│   │   └── urdf/
│   └── YOUR_MOVEIT_CONFIG_PACKAGE/   # 可选
├── .gitignore
└── README.md
```

包名、目录名和 `package://` 前缀必须一致。构建产物 `build/`、`install/`、`log/` 不属于源码，不要上传。

## 3. 从导出包到 Humble description 包

### 3.1 保存原始导出物

复制一份工作副本，保留原始 URDF、STL、CSV、日志和 SolidWorks 装配体。原始目录中的 Catkin 文件不要直接修改成 Humble 文件，这样可以在转换失败时回退和对照。

### 3.2 修正 URDF 通用问题

按照以下顺序检查：

1. 将包名改成小写英文字母、数字和下划线；
2. 将所有 visual/collision 网格改为 `package://包名/meshes/文件名.STL`；
3. 确认网格文件大小写完全一致；
4. 增加一个 `base_link` 和到实体底座的 fixed joint（如果原模型没有统一根）；
5. 检查 link/joint 树只有一个根、没有环路；
6. 检查 revolute/prismatic 的 axis、origin、limit、单位；
7. 删除单位不一致的错误 mimic；
8. 将 tool frame/TCP 作为明确的 fixed joint 添加，而不是移动 mesh 来“对齐”；
9. 只有在真实 CAD 或厂家资料支持时才修改质量、惯量和关节限位。

URDF 的位置单位是米，旋转角是弧度。`package://` 资源路径不能写 `C:\Users\...`、`/home/某个人/...` 或其他机器的绝对路径。

## 4. Humble 的 description 包

### 4.1 `package.xml`

使用 `ament_cmake`，执行依赖通常包括：

```xml
<exec_depend>ament_index_python</exec_depend>
<exec_depend>joint_state_publisher_gui</exec_depend>
<exec_depend>launch</exec_depend>
<exec_depend>launch_ros</exec_depend>
<exec_depend>robot_state_publisher</exec_depend>
<exec_depend>rviz2</exec_depend>
```

Gazebo、`ros2_control` 和 MoveIt 依赖应只加入实际使用它们的包。

### 4.2 `CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.8)
project(YOUR_DESCRIPTION_PACKAGE)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch meshes rviz urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
```

### 4.3 Python launch

Humble 推荐使用 `launch`/`launch_ros` 的 Python launch 文件。用 `get_package_share_directory()` 或 `Path` 读取安装后的 URDF 和 RViz 配置；不要硬编码本机路径。最小显示链仍然是：

```text
joint_state_publisher_gui
        ↓ /joint_states
robot_state_publisher
        ↓ /tf, /tf_static, /robot_description
rviz2
```

## 5. Humble 版本的坐标系说明

对于本仓库的 CR7AS Humble 模型，URDF 结构是：

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
                                    └── gripper_base  固定末端工具模型
                                        └── grasp_tcp_j [fixed]
                                            └── grasp_tcp 规划/TCP坐标系
```

含义如下：

- `base_link`：统一的根参考系；没有 visual/collision；
- `b0`：机械臂实际底座 link；
- `l1` 到 `l6`：六个活动关节后的机械臂 link；
- `gripper_base`：固定安装在 `l6` 上的末端模型，不是开合关节；
- `grasp_tcp`：用于抓取规划和工具中心点的坐标系，没有实体几何；
- `world`：只在 MoveIt SRDF 中作为 virtual joint 的父坐标系，未必是 URDF 中的实体 link。

当前模型没有夹爪开合 joint。不要把 `grasp_tcp` 误写成夹爪指爪，也不要把 `world` 当成机器人实体。需要真正的二指夹爪时，应按主动关节、从动关节、丝杠导程和闭环关系重新建模。

## 6. Gazebo Classic + ros2_control（可选）

如果目标是 Gazebo Classic，需要额外加入：

- `gazebo_ros2_control` 插件；
- URDF 中的 `ros2_control` 硬件和 interface；
- controller YAML；
- `gazebo_control.launch.py`；
- `controller_manager`、`joint_state_broadcaster` 和轨迹控制器依赖。

控制链应明确为：

```text
Gazebo /clock
  ├── robot_state_publisher (use_sim_time)
  ├── joint_state_broadcaster -> /joint_states
  └── arm_controller <- MoveIt trajectory
```

Gazebo Classic 和 Gazebo Sim 使用不同插件体系，不能只改包名后混用。

## 7. MoveIt 2 配置（可选）

MoveIt 2 建议使用独立配置包，至少包含：

```text
config/
├── robot.srdf
├── robot.urdf.xacro
├── kinematics.yaml
├── joint_limits.yaml
├── moveit_controllers.yaml
└── moveit.rviz
launch/
├── move_group.launch.py
└── moveit_rviz.launch.py
```

规划组的 base、tip 和控制器必须与 URDF 一致。当前 CR7AS 示例使用 `b0` 到 `grasp_tcp` 的 `ARM` 规划组，控制器动作名为 `/arm_controller/follow_joint_trajectory`。Gazebo 控制器由 Gazebo 启动链拥有时，MoveIt 不应再次接管控制器。

## 8. Humble 构建和验证

```bash
sudo apt update
sudo apt install \
  python3-colcon-common-extensions \
  ros-humble-joint-state-publisher-gui \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2

source /opt/ros/humble/setup.bash
cd ~/humble_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select YOUR_DESCRIPTION_PACKAGE
source install/setup.bash
ros2 launch YOUR_DESCRIPTION_PACKAGE display.launch.py
```

description 包验证通过后，再单独构建和启动 Gazebo/MoveIt 包：

```bash
colcon build --symlink-install --packages-select \
  YOUR_DESCRIPTION_PACKAGE \
  YOUR_MOVEIT_CONFIG_PACKAGE
source install/setup.bash
```

检查：

```bash
ros2 topic echo /joint_states --once
ros2 topic echo /clock --once                 # 使用仿真时才需要
ros2 node list
ros2 param get /move_group use_sim_time       # 使用 MoveIt 时检查
```

## 9. Foxy 与 Humble 的迁移差异

| 项目 | Foxy | Humble |
| --- | --- | --- |
| Ubuntu | 20.04 | 22.04 |
| description 构建 | `ament_cmake` + `colcon` | 基本相同 |
| launch | Python launch | Python launch，检查 API 和依赖版本 |
| RViz | `rviz2` | `rviz2` |
| Gazebo | 需明确选择 Classic 或 Sim | 同样需要明确选择，不能自动推断 |
| MoveIt | 另行配置 | 另行配置，确认 `moveit_configs_utils` 版本 |
| URDF 核心 | link/joint/mesh URI | 基本不变 |

因此，迁移的正确顺序是：先让 description 在 Humble 中显示，再添加仿真控制，最后添加 MoveIt 或硬件驱动。

## 10. 通用验收清单

- [ ] 原始 SW2URDF 导出物已单独备份；
- [ ] 包名、目录名、`package.xml` 和 `package://` 完全一致；
- [ ] 所有 mesh 文件存在且大小写一致；
- [ ] URDF 只有一个根、没有环、每个 child 只有一个父 joint；
- [ ] `base_link`、实体底座和末端/TCP 的语义已经写进 README；
- [ ] 没有把 `world`、`base_link` 或 `tcp` 误当成实体零件；
- [ ] description 包在目标发行版中构建并显示成功；
- [ ] Gazebo 使用正确的插件体系和仿真时钟；
- [ ] MoveIt 的规划组、tip 和控制器与 URDF 一致；
- [ ] 没有把显示测试限位或估算惯量直接用于真实硬件；
- [ ] CAD、STEP、STL 和机器人数据具有公开再分发授权。
