# SW21-URDF-STP

越疆 CR7AS 六轴机械臂与末端执行器的 SolidWorks、STEP、URDF 和 ROS 2 资料仓库。

本仓库同时保存两个 ROS 2 目标：

- **Foxy / RViz2 旧版**：用于从 SolidWorks 导出物转换成 ROS 2 description 包并检查 TF、网格和关节显示；
- **Humble 当前主线**：适用于 Ubuntu 22.04 + ROS 2 Humble，增加 Gazebo Classic、`ros2_control` 和 MoveIt 2 配置。

URDF 的 link、joint 和 mesh XML 在 Foxy/Humble 间基本通用；差异主要在构建依赖、launch、仿真控制链和 MoveIt 配置。请先阅读对应的通用模板，再阅读具体包的 README。

## 快速导航

| 目标 | 文档 |
| --- | --- |
| 总览和仓库布局 | 当前文档 |
| SolidWorks URDF -> ROS 2 Foxy 通用转换 | [`docs/ROS2_Foxy_URDF_通用转换模板.md`](docs/ROS2_Foxy_URDF_通用转换模板.md) |
| SolidWorks URDF -> ROS 2 Humble 通用转换 | [`docs/ROS2_Humble_URDF_通用转换模板.md`](docs/ROS2_Humble_URDF_通用转换模板.md) |
| 旧 Foxy/RViz2 包 | [`ROS2/RViz2/urdf_sw_description/README.md`](ROS2/RViz2/urdf_sw_description/README.md) |
| 当前 Humble 工作空间 | [`ROS2/Humble/README.md`](ROS2/Humble/README.md) |
| Humble CR7AS description 包 | [`ROS2/Humble/src/cr7as_grasp/README.md`](ROS2/Humble/src/cr7as_grasp/README.md) |
| Humble MoveIt 2 配置包 | [`ROS2/Humble/src/cr7as_grasp_moveit_config/README.md`](ROS2/Humble/src/cr7as_grasp_moveit_config/README.md) |

## 仓库布局

```text
SW21-URDF-STP/
├── README.md
├── docs/
│   ├── ROS2_Foxy_URDF_通用转换模板.md
│   └── ROS2_Humble_URDF_通用转换模板.md
├── SolidWorks/                       # CAD Pack and Go 文件
├── STEP/                             # STEP 交换模型
├── Images/                           # 模型预览图
├── URDF/URDF-ROS1/                   # SW2URDF 原始 ROS 1 导出资料
├── URDF/URDF-ROS2/                   # 旧 Foxy/RViz2 description 包
├── ROS2/RViz2/urdf_sw_description/   # 旧 Foxy/RViz2 包的工作空间副本
└── ROS2/Humble/                      # 当前 Humble 工作空间
    ├── README.md
    └── src/
        ├── cr7as_grasp/
        └── cr7as_grasp_moveit_config/
```

`URDF/URDF-ROS2/` 和 `ROS2/RViz2/urdf_sw_description/` 是旧 Foxy/RViz2 可视化资料的两个历史路径，内容用途相同。新的开发和仿真请使用 `ROS2/Humble/`，不要把旧包和 Humble 包放在同一个 ROS 工作空间的 `src/` 中一起构建。

## Foxy 版本：从 SolidWorks 导出物开始

旧 Foxy 包 `urdf_sw_description` 的模型拓扑是：

```text
base_link                         虚拟根坐标系
└── base_link_to_b0 [fixed]
    └── b0                         机械臂实体底座
        └── j1 -> l1
            └── j2 -> l2
                └── j3 -> l3
                    └── j4 -> l4
                        └── j5 -> l5
                            └── j6 -> l6
                                └── gripper_slider_joint [prismatic]
                                    └── gripper_link
```

这里的 `base_link` 只是统一 TF 根，`b0` 才是实体底座。旧 Foxy 模型没有真实的二指夹爪开合机构；`gripper_link` 和 `gripper_slider_joint` 是导出后整理出的末端可视化部件，不能自动解释为真实夹爪控制。如果模型没有末端工具，`l6` 可以直接作为末端 link；如果要添加工具，建议增加 `tool0` 和 `tcp` 两个 fixed frame，并在文档中写清楚相对位姿。

通用转换步骤见 [`docs/ROS2_Foxy_URDF_通用转换模板.md`](docs/ROS2_Foxy_URDF_通用转换模板.md)。

### Foxy 快速构建

```bash
source /opt/ros/foxy/setup.bash
mkdir -p ~/foxy_ws/src
cp -a ROS2/RViz2/urdf_sw_description ~/foxy_ws/src/
cd ~/foxy_ws
colcon build --symlink-install --packages-select urdf_sw_description
source install/setup.bash
ros2 launch urdf_sw_description display.launch.py
```

RViz2 中将 `Fixed Frame` 设置为 `base_link`，确认 `RobotModel` 为 `Ok`，再通过 Joint State Publisher GUI 检查 `j1` 到 `j6` 和 `gripper_slider_joint` 的显示行为。

## Humble 版本：当前 CR7AS 主线

Humble 工作空间只包含两个已经验证的功能包：

```text
ROS2/Humble/src/
├── cr7as_grasp/
└── cr7as_grasp_moveit_config/
```

拓扑为：

```text
base_link                         URDF 虚拟根
└── base_link_to_b0 [fixed]
    └── b0 -> l1 -> l2 -> l3 -> l4 -> l5 -> l6
        └── gripper_base_j [fixed]
            └── gripper_base       固定末端模型
                └── grasp_tcp_j [fixed]
                    └── grasp_tcp    工具/TCP坐标系
```

MoveIt SRDF 另外使用 `world` 作为 virtual joint 的父坐标系；`world` 不是 URDF 中的实体 link。当前 `gripper_base` 固定在 `l6` 上，`grasp_tcp` 没有 visual/collision，也没有夹爪开合关节。

### Humble 快速构建

```bash
source /opt/ros/humble/setup.bash
cd ROS2/Humble
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select \
  cr7as_grasp \
  cr7as_grasp_moveit_config
source install/setup.bash
```

启动 Gazebo Classic：

```bash
ros2 launch cr7as_grasp gazebo_control.launch.py
```

再在其他终端启动：

```bash
ros2 launch cr7as_grasp_moveit_config move_group.launch.py
ros2 launch cr7as_grasp_moveit_config moveit_rviz.launch.py
```

完整依赖、控制器检查、仿真时钟和限制见 [`ROS2/Humble/README.md`](ROS2/Humble/README.md)。

## CAD 和 STEP

- `SolidWorks/` 保存 SolidWorks Pack and Go 压缩包；解压时保持内部引用关系；
- `STEP/` 保存跨 CAD 软件交换用的 STEP 模型；
- SolidWorks、STEP、STL 和图片的公开再分发权限必须单独确认；
- GitHub 网页不能完整预览 SolidWorks 装配体，下载 CAD 时应使用 Git LFS。

## 文件和安全边界

- 不要提交 `build/`、`install/`、`log/`、Python 缓存或本地编辑器目录；
- 不要把旧 Foxy 包、Humble 包、Gazebo FakeSystem 和真实硬件驱动混在同一个工作空间中；
- 当前质量、惯量、关节限位、TCP 位姿和碰撞网格仍需结合厂家资料或实测校准；
- 不要把现场 IP、序列号、密码、标定数据或未经授权的 CAD/网格上传到公开仓库；
- RViz2 显示成功不等于可以驱动真实机械臂。

## 许可证

ROS 2 包中的代码和文档可以根据项目需要补充许可证，但 CAD、STEP、STL、图片和机器人数据的授权范围需要另行确认。在仓库添加完整 `LICENSE` 前，不应默认所有资源都允许复制、修改或商用。
