# SolidWorks 导出的 URDF 转 ROS 2 Foxy 通用模板

本文适用于从 SolidWorks SW2URDF 导出的 ROS 1/Catkin 风格包，目标是得到一个可以在 Ubuntu 20.04 + ROS 2 Foxy + RViz2 中构建、显示和检查的 description 包。

这不是把 URDF “转换成另一种 URDF 格式”。URDF 的 XML 结构基本不区分 Foxy 或 Humble；真正需要迁移的是包结构、资源路径、构建系统、启动文件和 RViz2 配置。

## 1. Foxy 目标和边界

完成本文后，目标包应能做到：

- `colcon build` 成功；
- `robot_state_publisher` 能发布完整 TF；
- RViz2 的 `RobotModel` 为 `Ok`；
- `joint_state_publisher_gui` 能显示每个主动关节的滑块；
- 所有 visual STL 能加载，且网格大小和姿态合理。

这仍然只是显示/描述包，不等于 Gazebo 物理仿真、MoveIt 2 规划或真实硬件控制。那些功能需要另外添加可靠的惯量、collision、控制器、驱动和安全参数。

## 2. 从 SolidWorks 导出后先做备份

保留一份只读的原始导出物，不直接在原始目录上修改：

```text
source_export/
├── 原始 URDF
├── meshes/
├── package.xml
├── CMakeLists.txt
├── launch/
└── 导出日志或 CSV
```

工作副本单独放在新的 ROS 2 包目录中。原始包中的 `catkin`、ROS 1 XML launch 和旧包名只作为对照，不要和 Foxy 包混装。

## 3. 推荐的 Foxy 包结构

```text
your_ws/
├── src/
│   └── YOUR_PACKAGE_NAME/
│       ├── CMakeLists.txt
│       ├── package.xml
│       ├── README.md
│       ├── launch/
│       │   └── display.launch.py
│       ├── config/
│       │   └── joint_names.yaml
│       ├── meshes/
│       │   └── *.STL
│       ├── rviz/
│       │   └── display.rviz
│       └── urdf/
│           └── YOUR_URDF_FILE.urdf
```

包名只使用小写英文字母、数字和下划线，例如 `cr7as_description`。包目录名、`package.xml` 的 `<name>`、`CMakeLists.txt` 的 `project()`、launch 中的包名，以及 URDF 中的 `package://` 前缀必须一致。

## 4. URDF 结构检查

### 4.1 网格路径

把所有 visual 和 collision 的路径统一为：

```xml
<mesh filename="package://YOUR_PACKAGE_NAME/meshes/link_1.STL" />
```

Linux 区分大小写。`link_1.STL`、`link_1.stl` 和实际文件名必须完全一致。每个 `filename=` 都要能在 `meshes/` 中找到对应文件。

### 4.2 根坐标系和关节树

SolidWorks 导出的第一个 link 通常是 `b0` 或类似名称。建议增加一个虚拟根 `base_link`：

```xml
<link name="base_link" />
<joint name="base_link_to_b0" type="fixed">
  <parent link="base_link" />
  <child link="b0" />
</joint>
```

`base_link` 是统一的参考坐标系，不是机器人实体；`b0` 才是带网格、质量和惯性的物理底座。除根 link 外，每个 link 只能有一个父 joint，整个 URDF 只能有一个根，不能形成环。

### 4.3 检查 link 和 joint

对每个 link 检查：

- `name` 唯一；
- visual 和 collision 的网格均存在；
- 惯性质量为正数，惯性矩为有限值；
- 一个 link 内的刚性零件已经合并，不要把同一零件重复放入两个 link。

对每个 joint 检查：

- `name` 唯一；
- `parent` 和 `child` 都引用已经声明的 link；
- revolute/prismatic 关节有正确的 `axis` 和 `limit`；
- `origin xyz` 使用米，`origin rpy` 使用弧度；
- 真实旋转中心和运动方向来自 SolidWorks 装配体，而不是靠移动 STL 来掩盖错误。

### 4.4 限位和 mimic

SW2URDF 常见问题是主动关节的 `lower` 与 `upper` 都为 0，或者把夹爪的 prismatic joint 错误地 mimic 到腕部旋转关节。显示测试可以临时给主动关节非零范围，但必须在 README 中标明“仅用于显示”，不能把临时值用于实机控制。

不同单位之间不能直接 mimic：旋转关节是弧度，直线关节是米。只有在机构比例已经明确、单位和方向都正确时才使用 `mimic`；非线性闭环夹爪应由专门控制节点或查表关系实现。

## 5. Foxy 版本的坐标系说明

一个没有末端工具的六轴机械臂可以使用：

```text
base_link                         虚拟根坐标系
└── base_link_to_b0 [fixed]
    └── b0                         机器人实体底座
        └── j1 -> l1
            └── j2 -> l2
                └── j3 -> l3
                    └── j4 -> l4
                        └── j5 -> l5
                            └── j6 -> l6   末端法兰/腕部 link
```

因此，Foxy 版本没有夹爪时，`l6` 可以作为末端 link；不要为了“看起来完整”凭空增加夹爪坐标系。

如果需要安装工具，推荐使用固定关节增加两个语义清晰的坐标系：

```text
l6
└── tool0 [fixed]                  工具安装面或工具基座
    └── tcp [fixed]                实际工具中心点
```

`tool0` 表示工具安装坐标系，`tcp` 表示工具中心点。两者的 `origin xyz/rpy` 必须来自真实装配尺寸。它们可以没有 visual/collision，但不能省略正确的父子关系。`base_link` 与 `b0` 是根部的两个不同语义：前者用于统一 TF，后者是实体底座；`l6`、`tool0` 和 `tcp` 是末端侧坐标系，不能混用。

本仓库的旧 Foxy 模型还包含 `gripper_link` 和 `gripper_slider_joint`。这表示一个可移动的末端模型，用于 RViz2 观察，并不等于已经建好了真实二指夹爪机构。它的结构是：

```text
l6 ── gripper_slider_joint [prismatic] ── gripper_link
```

如果实际模型没有末端夹爪，应删除这段或把末端明确设为 `l6`；如果保留，应在文档中说明行程、方向和是否只是显示用参数。

## 6. Foxy 的 ROS 2 文件

### 6.1 `package.xml`

至少需要 `ament_cmake`、`launch`、`launch_ros`、`robot_state_publisher`、`joint_state_publisher_gui`、`rviz2` 和 `ament_index_python` 的执行依赖。不要保留 ROS 1 的 `catkin`、`roslaunch` 或 `rviz` 依赖。

### 6.2 `CMakeLists.txt`

description 包至少应安装资源目录：

```cmake
cmake_minimum_required(VERSION 3.5)
project(YOUR_PACKAGE_NAME)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch meshes rviz urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
```

### 6.3 `display.launch.py`

启动三个节点：`joint_state_publisher_gui`、`robot_state_publisher` 和 `rviz2`。URDF 和 RViz 配置应使用 `get_package_share_directory()` 找到安装后的路径，不能写 Windows 或个人电脑的绝对路径。

### 6.4 `joint_names.yaml`

只列出需要独立发布的主动关节；不要加入 fixed joint，也不要把 mimic 从动关节误当成独立控制关节。

## 7. 构建和验证

```bash
sudo apt update
sudo apt install \
  python3-colcon-common-extensions \
  ros-foxy-joint-state-publisher-gui \
  ros-foxy-robot-state-publisher \
  ros-foxy-rviz2

source /opt/ros/foxy/setup.bash
cd ~/your_ws
colcon build --symlink-install --packages-select YOUR_PACKAGE_NAME
source install/setup.bash
ros2 launch YOUR_PACKAGE_NAME display.launch.py
```

RViz2 中将 `Fixed Frame` 设置为 `base_link`，检查 `RobotModel` 为 `Ok`，再执行：

```bash
ros2 topic echo /joint_states --once
ros2 node list
ros2 run tf2_tools view_frames
```

完成验收后再考虑 Gazebo、MoveIt 2 或真实控制。显示包中的 effort、velocity、惯量和限位不能自动视为厂家参数。

## 8. 常见问题

| 现象 | 优先检查 |
| --- | --- |
| `Package ... not found` | 是否构建并 `source install/setup.bash`，包名是否一致 |
| RobotModel 为空 | Fixed Frame、URDF XML 和 `package://` 网格路径 |
| 只有 TF 没有实体 | visual 网格是否存在，CMake 是否安装 `meshes/` |
| 滑块不出现 | 关节是否为 fixed，或者 lower/upper 是否都为 0 |
| 方向错误 | joint 的 `origin`、局部 `axis` 和 SolidWorks 坐标系 |
| 模型大小错误 | SolidWorks 导出单位和 STL 是否需要 `scale="0.001 0.001 0.001"` |
| 夹爪跟随腕部错误运动 | 删除错误 mimic，按真实丝杠/闭环关系重新建模 |
