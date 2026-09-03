# SolidWorks 2021 导出的 URDF 转为 ROS 2 Foxy / RViz2 可完整显示的通用模板

> **适用目标**：把由 **SolidWorks 2021 + SolidWorks to URDF Exporter** 导出的机械臂 URDF、STL 网格和关节信息，整理为一个可被 **ROS 2 Foxy（Ubuntu 20.04）** 构建，并能通过 `ros2 launch` 在 **RViz2** 中完整显示、使用滑块查看关节姿态的 description 功能包。
>
> **本模板不等于真实机械臂控制。** 本文完成的是“模型描述 + TF + RViz2 可视化”。要控制实体机械臂、做碰撞规划或物理仿真，还需分别配置厂商驱动、`ros2_control`、MoveIt 2、Gazebo 等内容。

---

## 目录

1. [先理解最终要得到什么](#1-先理解最终要得到什么)
2. [开始前的版本、软件和目录规范](#2-开始前的版本软件和目录规范)
3. [SolidWorks 导出后先检查什么](#3-solidworks-导出后先检查什么)
4. [从 ROS 1 风格导出物改为 ROS 2 Foxy 包](#4-从-ros-1-风格导出物改为-ros-2-foxy-包)
5. [URDF 必改项（原因、示例、验证）](#5-urdf-必改项原因示例验证)
6. [ROS 2 功能包文件模板](#6-ros-2-功能包文件模板)
7. [构建、启动与 RViz2 设置](#7-构建启动与-rviz2-设置)
8. [常见报错排查表](#8-常见报错排查表)
9. [DOBOT CR7 实际改动对照案例](#9-dobot-cr7-实际改动对照案例)
10. [显示成功后还能做什么](#10-显示成功后还能做什么)
11. [最终交付检查清单](#11-最终交付检查清单)

---

## 1. 先理解最终要得到什么

### 1.1 最终运行链路

```text
SolidWorks 装配体
  ↓（SolidWorks to URDF Exporter 导出）
URDF + STL/DAE 网格 + ROS 1 风格 package/launch（常见）
  ↓（修改命名、mesh 路径、根坐标系、关节限位、ROS 2 包文件）
ROS 2 description 功能包
  ↓（colcon build）
robot_description 参数
  ├─ joint_state_publisher_gui：发布各活动关节的角度 /joint_states
  ├─ robot_state_publisher：根据 URDF + /joint_states 发布 /tf
  └─ RViz2：读取 robot_description 和 /tf，显示机械臂
```

### 1.2 “完整显示”至少包含的结果

- RViz2 中能看到所有 link 的 STL 网格，而不是空白或只有局部。
- RViz2 的 `RobotModel` 状态为 **Ok**。
- `Fixed Frame` 能设为 `base_link`（或你定义的根 link）。
- `joint_state_publisher_gui` 出现每一个可动关节的滑块。
- 拖动 `j1`～`j6` 等滑块时，模型姿态会随之改变。
- TF 树是连通的：例如 `base_link → l0 → l1 → ... → l6`。

### 1.3 必须区分的四个层次

| 层次 | 本模板是否完成 | 说明 |
|---|---:|---|
| RViz2 显示 | 是 | 只用于观察模型、坐标系和关节姿态。 |
| `joint_state_publisher_gui` 滑块运动 | 是 | 是人为发布关节角度，不会驱动真实电机。 |
| Gazebo 物理仿真 | 否 | 需要合理的惯量、碰撞体、摩擦、传动、Gazebo 插件等。 |
| MoveIt 2 / 真实机械臂 | 否 | 需要真实限位、运动学、控制器、通信和安全措施。 |

> ⚠️ 因此，**能在 RViz2 中动，不代表实体机械臂能够安全地动。**

---

## 2. 开始前的版本、软件和目录规范

### 2.1 本文示例环境

| 项目 | 示例 |
|---|---|
| 建模软件 | SolidWorks 2021 |
| 操作系统 | Ubuntu 20.04（代号 `focal`） |
| ROS 2 | Foxy |
| ROS 工作空间 | `~/Desktop/dev_ws` |
| ROS 2 包类型 | `ament_cmake` description 包 |

加载环境：

```bash
source /opt/ros/foxy/setup.bash
```

如果下面命令不存在，先确认 ROS 版本：

```bash
ls /opt/ros
echo $ROS_DISTRO
```

预期能看到 `foxy`。如果你的 `/opt/ros` 中只有 `foxy`，就**不能**使用 `source /opt/ros/humble/setup.bash`。

### 2.2 ROS 2 功能包命名规则

建议只用：**小写字母、数字、下划线**。

| 不推荐 / 常导致问题 | 推荐 |
|---|---|
| `DOBOT CR7Model` | `dobot_cr7_description` |
| 包名含空格 | 不含空格 |
| 包名含大写 | 全小写 |
| 包名与 URDF 中 `package://` 不一致 | 两者严格一致 |

推荐用途命名：

```text
品牌_型号_description
例如：dobot_cr7_description
```

### 2.3 推荐目录结构

一个只负责显示的 ROS 2 description 包可按如下组织：

```text
dobot_cr7_description/
├── CMakeLists.txt
├── package.xml
├── README.md
├── config/
│   └── joint_names.yaml              # 可选：以后接控制器时使用
├── launch/
│   └── display.launch.py
├── meshes/
│   ├── l0.STL
│   ├── l1.STL
│   └── ...
├── textures/                         # 可选；没有纹理就不要创建/安装它
└── urdf/
    └── dobot_cr7.urdf
```

> **关键原则**：不要只复制 `.urdf` 文件。URDF 中引用的所有 `meshes/*.STL` 或 `textures/*` 文件，也必须一同带入包内，并在 `CMakeLists.txt` 安装到 `share/${PROJECT_NAME}`。

---

## 3. SolidWorks 导出后先检查什么

SolidWorks to URDF Exporter 常导出以下内容：

```text
模型目录/
├── urdf/
│   └── 原始模型.urdf
├── meshes/
│   ├── link1.STL
│   ├── link2.STL
│   └── ...
├── launch/                           # 经常是 ROS 1 XML launch
├── config/                           # 可能有 joint_names.yaml
├── package.xml                       # 经常是 ROS 1 catkin 版本
└── CMakeLists.txt                    # 经常是 ROS 1 catkin 版本
```

### 3.1 第一次检查表

| 检查项 | 怎么看 | 结果不对时的后果 |
|---|---|---|
| URDF 是否存在 | `urdf/xxx.urdf` | 没有模型结构文件。 |
| STL 是否齐全 | `meshes/` 中文件数与 URDF `<mesh>` 引用数大致相符 | RViz2 缺零件或完全空白。 |
| `<robot name>` | 打开 URDF 顶部 | 与包名不同不一定报错，但建议统一且合法。 |
| `<mesh filename>` | 搜索 `filename=` | `package://` 包名错误会找不到网格。 |
| link / joint 数量 | 搜索 `<link` 与 `<joint` | 漏关节、父子 link 写错会造成 TF 树断裂。 |
| 关节类型与 axis | 查看 `<joint type>`、`<axis xyz>` | 模型旋转方向不对。 |
| 限位 | 查看 `<limit lower=... upper=...>` | 全为 0 时滑块无法运动。 |
| 单位 | 查看导出选项、在 RViz2 看比例 | 常见为 mm / m 混淆，模型会异常大或小。 |

### 3.2 先备份原始导出物

不要直接覆盖 SolidWorks 的原始导出目录。建议保留两份：

```text
原始导出：DOBOT CR7Model/                 # 不改，便于回退
ROS 2 整理后：dobot_cr7_description/       # 在此目录中修改
```

---

## 4. 从 ROS 1 风格导出物改为 ROS 2 Foxy 包

### 4.1 URDF 本身不是“ROS 1 或 ROS 2 专属”

URDF 是 XML 机器人描述格式，很多内容可以直接沿用，例如：

- `<link>`、`<joint>`、`<origin>`、`<axis>`；
- `<visual>`、`<collision>`、`<inertial>`；
- STL 网格文件。

真正需要从 ROS 1 改到 ROS 2 的主要是：

1. `package.xml`：从 `catkin` 改为 `ament_cmake`；
2. `CMakeLists.txt`：从 catkin 宏改为 ament；
3. launch：从 ROS 1 XML 改为 ROS 2 Python launch；
4. `package://包名/...`：同步为新的 ROS 2 包名；
5. 构建命令：`catkin_make` 改为 `colcon build`。

### 4.2 创建 ROS 2 目标包目录

在 Ubuntu 工作空间中：

```bash
source /opt/ros/foxy/setup.bash
mkdir -p ~/Desktop/dev_ws/src
cd ~/Desktop/dev_ws/src
mkdir -p your_robot_description/{urdf,meshes,launch,config}
```

把原始 `.urdf` 和所有网格复制进去。若原始模型位于 Windows 共享盘或 U 盘，请先确认它在 Ubuntu 的实际挂载路径；**Windows 的 `H:\...` 不能直接作为 Ubuntu 终端路径使用。**

示例（路径按实际挂载位置替换）：

```bash
cp -r /media/$USER/USB/your_robot_description ~/Desktop/dev_ws/src/
```

---

## 5. URDF 必改项（原因、示例、验证）

> 下面每项都是一个可复用的检查模板。修改前先备份：
>
> ```bash
> cp urdf/your_robot.urdf urdf/your_robot.urdf.bak
> ```

### 5.1 修改 `<robot name>` 和资源包名

#### 为什么要改

SolidWorks 项目名称常包含空格和大写，例如 `DOBOT CR7Model`。ROS 2 包名不能这样使用；而网格路径又依赖包名，所以必须统一。

#### 修改前示例

```xml
<robot name="DOBOT CR7Model">

<mesh filename="package://DOBOT CR7Model/meshes/l0.STL" />
```

#### 修改后示例

```xml
<robot name="dobot_cr7">

<mesh filename="package://dobot_cr7_description/meshes/l0.STL" />
```

#### 如何验证

在 URDF 中搜索：

```bash
grep -n 'package://' urdf/dobot_cr7.urdf
```

输出中的每一行都必须使用同一个真实包名：

```text
package://dobot_cr7_description/meshes/...
```

#### 常见错误

- 目录改名了，URDF 内的 `package://旧包名/` 没改；
- `package.xml` 叫 `dobot_cr7_description`，但 launch 或 URDF 写成 `dobot_cr7`；
- `STL` 与 `stl` 大小写混用。Linux 路径大小写敏感。

---

### 5.2 确保每个 mesh 文件都在正确位置

#### 为什么要改

RViz2 读取 `<visual>` 时，会根据 `package://包名/相对路径` 查找 STL。只要包名、目录、文件名三者之一不一致，RViz2 就会显示不完整或报 “resource not found”。

#### 修改前示例

```xml
<mesh filename="package://DOBOT CR7Model/meshes/l3.STL" />
```

但是实际文件已移动为：

```text
dobot_cr7_description/meshes/l3.STL
```

#### 修改后示例

```xml
<mesh filename="package://dobot_cr7_description/meshes/l3.STL" />
```

#### 如何验证

```bash
# 确认文件存在
ls ~/Desktop/dev_ws/src/dobot_cr7_description/meshes

# 构建、source 后确认安装副本也存在
ls ~/Desktop/dev_ws/install/dobot_cr7_description/share/dobot_cr7_description/meshes
```

#### 补充：STL 单位 / 比例问题

如果显示出来的机械臂极大、极小或看起来被截断，先怀疑 SolidWorks 导出单位。

可以在 `<mesh>` 加 `scale` 进行临时显示校正，例如原 STL 以毫米为单位、而 ROS 使用米时：

```xml
<mesh filename="package://your_robot_description/meshes/link1.STL"
      scale="0.001 0.001 0.001" />
```

> 这只是临时修正方式。最优先的方案是在 SolidWorks 导出时确认单位为 **meter（米）**，并使视觉网格、碰撞网格、关节 `<origin xyz>` 使用同一单位体系。

---

### 5.3 给模型增加一个统一根坐标系 `base_link`

#### 为什么要改

机械臂通常需要一个稳定的世界/底座参考坐标系。SolidWorks 导出时可能直接从 `l0` 开始，虽然 URDF 仍可合法，但 RViz2、TF、MoveIt 以及后续控制配置通常更容易以 `base_link` 作为根。

#### 修改前示例

导出的第一个 link 直接是：

```xml
<link name="l0">
  ...
</link>
```

而没有顶层底座坐标。

#### 修改后示例

把以下内容加在 `<robot ...>` 内、`l0` 之前：

```xml
<!-- 给模型添加统一根坐标系；l0 是 SolidWorks 导出的原始底座 -->
<link name="base_link" />

<joint name="base_link_to_l0" type="fixed">
  <parent link="base_link" />
  <child link="l0" />
  <origin xyz="0 0 0" rpy="0 0 0" />
</joint>
```

如果机械臂模型的原点不在期望的地面/底座中心，可在 `origin` 中调整，但第一次显示建议先保持全 0：

```xml
<origin xyz="0 0 0" rpy="0 0 0" />
```

#### 如何验证

启动后：

```bash
ros2 run tf2_ros tf2_echo base_link l6
```

如果最后一个 link 不是 `l6`，替换为你的末端 link 名。能连续输出变换，说明 TF 链已连通。

#### 常见错误

- 加了 `base_link`，却忘记用 fixed joint 接到原始第一个 link；这样会产生两个根；
- `parent` / `child` 写反，模型方向或树结构会异常；
- 同一个 child link 被两个 joint 指向，URDF 树会非法。

---

### 5.4 检查 link、joint、父子关系是否形成一棵树

#### 为什么要改

`robot_state_publisher` 需要一个无环、单根、连通的机器人树。每个活动 joint 都要把一个父 link 接到一个子 link。

#### 正确的串联机械臂示例

```text
base_link
  └──(fixed) base_link_to_l0 → l0
        └──(revolute) j1 → l1
              └──(revolute) j2 → l2
                    └──(revolute) j3 → l3
```

对应一个关节：

```xml
<joint name="j1" type="revolute">
  <origin xyz="0 0 0.0713" rpy="0 0 0" />
  <parent link="l0" />
  <child link="l1" />
  <axis xyz="0 0 -1" />
  <limit lower="-1.57" upper="1.57" effort="10.0" velocity="1.0" />
</joint>
```

#### 如何验证

- 每个 `<parent link="..."/>` 和 `<child link="..."/>` 指向的 link 都必须存在；
- 除根 link 外，每个 link 应恰好有一个父 joint；
- 树不能形成环，例如 `l1 → l2 → l1`；
- `revolute` / `prismatic` 关节要有 `axis` 与 `limit`。

---

### 5.5 修改被 SolidWorks 锁死的关节限位

#### 为什么要改

有些 SolidWorks 导出模型会把活动关节写成：

```xml
<limit lower="0" upper="0" effort="0" velocity="0" />
```

这意味着关节没有任何活动范围，所以 `joint_state_publisher_gui` 中即使出现滑块，也无法让机械臂动。

#### 修改前示例

```xml
<joint name="j1" type="revolute">
  <axis xyz="0 0 -1" />
  <limit lower="0" upper="0" effort="0" velocity="0" />
</joint>
```

#### 修改后示例 A：仅用于 RViz2 显示测试

```xml
<joint name="j1" type="revolute">
  <axis xyz="0 0 -1" />
  <limit
    lower="-3.14159265359"
    upper="3.14159265359"
    effort="10.0"
    velocity="1.0" />
</joint>
```

这里 `-3.14159265359` 到 `3.14159265359` 等于约 `-180°` 到 `+180°`。它便于观察模型，**不是厂家确认的真实 CR7 安全范围**。

#### 修改后示例 B：用于后续规划 / 控制前的真实值写法

```xml
<!-- 以下数值仅为格式示例，必须替换成厂家手册确认的 j1 数据 -->
<limit
  lower="-2.967"
  upper="2.967"
  effort="实际允许力矩或控制器约束值"
  velocity="实际允许角速度" />
```

#### 如何验证

启动 `joint_state_publisher_gui` 后：

- 滑块应有非零范围；
- 拖动滑块，RViz2 中对应 link 应旋转；
- 若方向相反，检查 `axis xyz` 的正负号，而不是随意交换 parent/child。

> ⚠️ **安全提醒**：假设的 `±π` 仅可用于 RViz2 看图。接入实体机械臂前，必须以越疆官方说明书、SDK 和控制器的实际限制为准。

---

### 5.6 检查 `<axis>`，理解为什么会“往反方向转”

#### 为什么要改

关节的旋转轴由：

```xml
<axis xyz="x y z" />
```

定义，且它是在**关节坐标系**中定义的，不一定等于世界坐标系。轴向相反就会造成 GUI 正值转向与预期相反。

#### 示例

```xml
<!-- 绕关节局部 Z 轴正方向旋转 -->
<axis xyz="0 0 1" />

<!-- 与上面方向相反 -->
<axis xyz="0 0 -1" />
```

如果机械臂姿态看起来不对，推荐排查顺序：

1. 先确认 SolidWorks 装配体中每个关节轴；
2. 检查 `<origin xyz="..." rpy="..."/>`；
3. 最后才测试 `axis` 的正负号；
4. 不要为“反转方向”而错误交换 `<parent>` 和 `<child>`。

---

### 5.7 保留并检查 `visual`、`collision`、`inertial`

#### `visual`：RViz2 显示必须有

```xml
<visual>
  <origin xyz="0 0 0" rpy="0 0 0" />
  <geometry>
    <mesh filename="package://your_robot_description/meshes/link1.STL" />
  </geometry>
  <material name="light_gray">
    <color rgba="0.7 0.7 0.7 1.0" />
  </material>
</visual>
```

没有 `<visual>`，即使 TF 正常，RViz2 也看不到对应零件。

#### `collision`：为后续碰撞检测准备

```xml
<collision>
  <origin xyz="0 0 0" rpy="0 0 0" />
  <geometry>
    <mesh filename="package://your_robot_description/meshes/link1.STL" />
  </geometry>
</collision>
```

RViz2 单纯显示可先使用与 `visual` 相同的网格；但后续 MoveIt/Gazebo 建议使用更简单的碰撞模型，否则运算会很慢。

#### `inertial`：影响仿真，不是 RViz2 显示的必要条件

```xml
<inertial>
  <origin xyz="0.0 0.0 0.05" rpy="0 0 0" />
  <mass value="1.2" />
  <inertia ixx="0.01" ixy="0" ixz="0"
           iyy="0.01" iyz="0" izz="0.005" />
</inertial>
```

- RViz2 显示主要使用 `visual`；
- Gazebo / 动力学会依赖质量和惯量；
- 不清楚真实质量与惯量时，不要把猜测值用于真实控制或可信动力学结论；
- SolidWorks 自动导出的质量与惯量需确认材质、零件密度、单位和装配体状态后才能信任。

---

### 5.8 固定关节与活动关节的选择

| 机械结构 | URDF 类型 | 是否需要 `<limit>` |
|---|---|---:|
| 焊死的底座连接 | `fixed` | 否 |
| 旋转电机关节 | `revolute` 或 `continuous` | `revolute` 需要 |
| 丝杠/滑台直线关节 | `prismatic` | 需要 |
| 无机械限位、可无限旋转 | `continuous` | 通常不写位置范围 |

示例：

```xml
<!-- 底座固定 -->
<joint name="base_link_to_l0" type="fixed"> ... </joint>

<!-- 有有限机械范围的旋转关节 -->
<joint name="joint_1" type="revolute"> ... </joint>
```

> 对工业机械臂来说，是否写 `continuous` 必须根据实体机械限位和厂家定义，不要仅凭“看起来能转一圈”判断。

---

## 6. ROS 2 功能包文件模板

以下内容可直接作为一个 **仅用于 RViz2 显示** 的 ROS 2 Foxy description 包基础模板。将包名、URDF 文件名替换成自己的名称。

### 6.1 `package.xml` 模板

文件：`your_robot_description/package.xml`

```xml
<?xml version="1.0"?>
<package format="3">
  <name>your_robot_description</name>
  <version>0.0.1</version>
  <description>ROS 2 URDF description package for your robot.</description>

  <maintainer email="your_email@example.com">your_name</maintainer>
  <license>BSD-3-Clause</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <exec_depend>ament_index_python</exec_depend>
  <exec_depend>joint_state_publisher_gui</exec_depend>
  <exec_depend>launch</exec_depend>
  <exec_depend>launch_ros</exec_depend>
  <exec_depend>robot_state_publisher</exec_depend>
  <exec_depend>rviz2</exec_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

#### 与 ROS 1 导出版本相比要改什么

ROS 1 常见写法：

```xml
<buildtool_depend>catkin</buildtool_depend>
```

ROS 2 Foxy 要改为：

```xml
<buildtool_depend>ament_cmake</buildtool_depend>
```

并用 `exec_depend` 声明运行 launch 所依赖的软件包。

---

### 6.2 `CMakeLists.txt` 模板

文件：`your_robot_description/CMakeLists.txt`

```cmake
cmake_minimum_required(VERSION 3.5)
project(your_robot_description)

find_package(ament_cmake REQUIRED)

# 只写实际存在的目录。
install(
  DIRECTORY config launch meshes urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
```

#### 为什么必须安装这些目录

`colcon build` 不会自动把 `urdf/`、`meshes/`、`launch/` 当作程序安装。若不写上面的 `install(DIRECTORY ...)`，构建后 `ros2 launch` 找不到 launch 文件，或 RViz2 找不到 `package://.../meshes/*.STL`。

#### 常见错误：写了不存在的目录

```cmake
install(
  DIRECTORY config launch meshes textures urdf
  DESTINATION share/${PROJECT_NAME}
)
```

如果包内没有 `textures/`，建议删除 `textures`；若确实有纹理目录则保留。

改为：

```cmake
install(
  DIRECTORY config launch meshes urdf
  DESTINATION share/${PROJECT_NAME}
)
```

---

### 6.3 `display.launch.py` 模板

文件：`your_robot_description/launch/display.launch.py`

```python
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('your_robot_description')
    urdf_path = os.path.join(package_share, 'urdf', 'your_robot.urdf')

    with open(urdf_path, 'r') as urdf_file:
        robot_description = urdf_file.read()

    return LaunchDescription([
        # 用 GUI 滑块发布各可动关节的位置到 /joint_states
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen',
            parameters=[{'robot_description': robot_description}],
        ),

        # 根据 URDF 与 /joint_states 发布 TF
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description}],
        ),

        # 打开可视化界面
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
        ),
    ])
```

#### 必须同步替换的三处

```python
get_package_share_directory('your_robot_description')
#                           ↑ 与 package.xml 和文件夹名一致

os.path.join(package_share, 'urdf', 'your_robot.urdf')
#                                      ↑ 与实际 URDF 文件名一致
```

启动时：

```bash
ros2 launch your_robot_description display.launch.py
#           ↑ 与 package.xml 的 <name> 一致
```

---

### 6.4 可选的 `config/joint_names.yaml`

文件：`your_robot_description/config/joint_names.yaml`

```yaml
controller_joint_names: [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6]
```

它在本模板的 RViz2 显示 launch 中**没有被使用**，但保留它有利于后续接控制器。

常见错误：

```yaml
controller_joint_names: ['', joint_1, joint_2]
```

应删掉空字符串：

```yaml
controller_joint_names: [joint_1, joint_2]
```

并确保每个名字都和 URDF 的 `<joint name="...">` 完全一致。

---

## 7. 构建、启动与 RViz2 设置

### 7.1 安装显示所需的软件包

在 Ubuntu 20.04 + ROS 2 Foxy：

```bash
sudo apt update
sudo apt install ros-foxy-robot-state-publisher \
                 ros-foxy-joint-state-publisher-gui \
                 ros-foxy-rviz2
```

### 7.2 放入工作空间并构建

目标结构：

```text
~/Desktop/dev_ws/
└── src/
    └── dobot_cr7_description/
        ├── package.xml
        ├── CMakeLists.txt
        ├── urdf/
        ├── meshes/
        └── launch/
```

构建命令：

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/dev_ws
colcon build --symlink-install --packages-select dobot_cr7_description
source install/setup.bash
```

解释：

| 命令 | 作用 |
|---|---|
| `source /opt/ros/foxy/setup.bash` | 加载 ROS 2 Foxy 基础环境。 |
| `colcon build` | 编译/安装工作空间包。 |
| `--symlink-install` | 开发时使用软链接，修改多数资源文件后更方便；改包配置后仍建议重新 build。 |
| `--packages-select ...` | 只构建指定包，排错更快。 |
| `source install/setup.bash` | 让当前终端识别刚构建完成的包。 |

### 7.3 启动

```bash
ros2 launch dobot_cr7_description display.launch.py
```

### 7.4 RViz2 第一次设置

RViz2 打开后按下面设置：

1. 左侧 `Global Options`；
2. 将 **Fixed Frame** 改成：

   ```text
   base_link
   ```

3. 点击 `Add`；
4. 添加 `RobotModel`；
5. 可再添加 `TF`，查看每个坐标系；
6. 在 `joint_state_publisher_gui` 窗口拖动关节滑块，观察模型是否运动。

### 7.5 终端验证命令

另开一个已 source 的终端：

```bash
source /opt/ros/foxy/setup.bash
source ~/Desktop/dev_ws/install/setup.bash

# 查看节点
ros2 node list

# 应能看到 joint state 数据
ros2 topic echo /joint_states --once

# 查看 TF 坐标变换（末端 link 名按实际替换）
ros2 run tf2_ros tf2_echo base_link l6
```

可以生成 TF 结构图（需安装 `ros-foxy-tf2-tools`）：

```bash
ros2 run tf2_tools view_frames.py
```

> 命令是 `tf2_tools` 和 `view_frames.py`，中间是下划线，不是 `tf2 tools view frames.py`。

---

## 8. 常见报错排查表

| 现象 / 报错 | 最可能原因 | 解决方法 |
|---|---|---|
| `Package ... not found` | 没 build、没 source `install/setup.bash`、包名不一致 | `colcon build --packages-select 包名` 后执行 `source install/setup.bash`；检查 `<name>`。 |
| `file ... .urdf does not exist` | launch 中的 URDF 文件名/路径不对 | 核对 `os.path.join(..., 'urdf', '文件名.urdf')`。 |
| RViz2 空白，RobotModel 不是 Ok | 固定坐标系错、URDF 没加载、mesh 路径错 | Fixed Frame 设为 `base_link`；看终端错误；检查 `package://`。 |
| 有坐标系，没有机械臂实体 | link 缺 `<visual>` 或 STL 找不到 | 为 link 添加 `<visual>`；核对网格文件名、大小写、安装目录。 |
| 只有一部分机械臂 | 某些 STL 没复制或路径错误 | 对照每条 `<mesh filename>`，确认每个文件都存在。 |
| GUI 没有滑块或拖动不动 | joint 是 `fixed`，或 `lower=upper=0` | 可动关节用 `revolute`/`prismatic`；设置非零范围。 |
| 滑块动了但模型方向反 | `<axis>` 方向不对，或 joint `<origin rpy>` 不正确 | 按顺序检查装配体轴、origin、axis 正负。 |
| 模型巨大/微小 | mm 和 m 单位混用 | 优先重新按米导出；临时使用 mesh `scale="0.001 0.001 0.001"`。 |
| `joint_state_publisher_gui` 找不到 | ROS 软件包未装 | 安装 `ros-foxy-joint-state-publisher-gui`。 |
| 构建时 `catkin` 错误 | 仍是 ROS 1 的 package.xml/CMake | 替换为本模板的 `ament_cmake` 版本。 |
| `launch` 报 Python 缩进错误 | `.py` 文件缩进损坏 | 使用 4 个空格；不要混入 Tab。 |
| 生成的 TF 树断开 | 某个 joint 的 parent/child link 名写错 | 检查 link 名、父子关系，保证一棵单根树。 |
| `resource not found` / 找不到 STL | 包名不一致、未 install meshes、文件后缀大小写不一致 | 改 `package://`；确认 CMake 安装 `meshes`；检查 `.STL`。 |

---

## 9. DOBOT CR7 实际改动对照案例

本节记录本次 **DOBOT CR7** 从 SolidWorks 导出到 ROS 2 Foxy / RViz2 显示时实际采用的改动，后续可作为新模型的参照。

### 9.1 实际路径与文件

整理后的 ROS 2 包：

```text
H:\Desktop\rosstudy\dobot_cr7_description
```

主要文件：

```text
dobot_cr7_description/
├── urdf/dobot_cr7.urdf
├── meshes/l0.STL ... l6.STL
├── launch/display.launch.py
├── config/joint_names.yaml
├── package.xml
└── CMakeLists.txt
```

机械臂链：

```text
base_link
  └── base_link_to_l0 (fixed)
        └── l0
              └── j1 → l1
                    └── j2 → l2
                          └── j3 → l3
                                └── j4 → l4
                                      └── j5 → l5
                                            └── j6 → l6
```

### 9.2 实际改动 1：包名从带空格的大写名称改为 ROS 2 合法包名

**原 SolidWorks 项目名称：**

```text
DOBOT CR7Model
```

**改为：**

```text
dobot_cr7_description
```

**URDF 中对应修改：**

```xml
<!-- 改前（示意） -->
<mesh filename="package://DOBOT CR7Model/meshes/l0.STL" />

<!-- 改后（实际形式） -->
<mesh filename="package://dobot_cr7_description/meshes/l0.STL" />
```

这个替换必须对 `l0.STL` 到 `l6.STL` 的所有 visual/collision mesh 一并完成。

### 9.3 实际改动 2：增加 `base_link` 和固定连接

SolidWorks 导出的模型从 `l0` 开始。为使 ROS 2 / RViz2 有统一根坐标系，在 `dobot_cr7.urdf` 的 `<robot>` 内加入：

```xml
<link name="base_link" />

<joint name="base_link_to_l0" type="fixed">
  <parent link="base_link" />
  <child link="l0" />
  <origin xyz="0 0 0" rpy="0 0 0" />
</joint>
```

之后 RViz2 的 `Fixed Frame` 可设置为：

```text
base_link
```

### 9.4 实际改动 3：解除 6 个旋转关节的“零限位锁定”

导出模型中 `j1`～`j6` 的关节限位为零时，会锁死滑块。为 **RViz2 显示测试**，将每个关节从：

```xml
<limit lower="0" upper="0" effort="0" velocity="0" />
```

临时改为：

```xml
<limit
  lower="-3.14159265359"
  upper="3.14159265359"
  effort="10.0"
  velocity="1.0" />
```

例如 CR7 的 `j1` 结构是：

```xml
<joint name="j1" type="revolute">
  <origin xyz="0 -0.000216368625013428 0.0713" rpy="0 0 0" />
  <parent link="l0" />
  <child link="l1" />
  <axis xyz="0 0 -1" />
  <limit
    lower="-3.14159265359"
    upper="3.14159265359"
    effort="10.0"
    velocity="1.0" />
</joint>
```

> ⚠️ 以上范围仅为 RViz2 演示范围，**不是 DOBOT CR7 的真实运动范围**。今后配置 MoveIt、Gazebo、`ros2_control` 或真实机械臂前，应查询并填写越疆对应型号、固件和控制模式下的正式关节限制。

### 9.5 实际改动 4：ROS 1 catkin 包改为 ROS 2 ament 包

ROS 2 版本的 `package.xml` 使用：

```xml
<buildtool_depend>ament_cmake</buildtool_depend>
```

而不是 ROS 1 的：

```xml
<buildtool_depend>catkin</buildtool_depend>
```

对应 `CMakeLists.txt` 的核心内容：

```cmake
find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch meshes urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
```

### 9.6 实际改动 5：采用 ROS 2 Python launch

本次的 launch 文件：

```text
launch/display.launch.py
```

做了三件事：

1. 读取安装后的 `urdf/dobot_cr7.urdf`；
2. 启动 `joint_state_publisher_gui` 和 `robot_state_publisher`；
3. 启动 RViz2。

这与 ROS 1 常见的 XML `.launch` 文件不同。

### 9.7 实际改动 6：修正关节名称列表

使用：

```yaml
controller_joint_names: [j1, j2, j3, j4, j5, j6]
```

不使用空名称：

```yaml
controller_joint_names: ['', j1, j2, j3, j4, j5, j6]
```

### 9.8 实际运行命令

在 Ubuntu 中将整理后的包放入：

```text
~/Desktop/dev_ws/src/dobot_cr7_description
```

执行：

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/dev_ws
colcon build --symlink-install --packages-select dobot_cr7_description
source install/setup.bash
ros2 launch dobot_cr7_description display.launch.py
```

最终验证标准：RViz2 中添加 `RobotModel` 后，状态为 **Ok**；`joint_state_publisher_gui` 的 `j1`～`j6` 滑块能带动模型显示姿态变化。

---

## 10. 显示成功后还能做什么

### 10.1 加末端工具 / 二指夹爪

正确思路是：

1. 为夹爪创建自己的 link 和 joint；
2. 用 `fixed` joint 把夹爪基座连接到机械臂末端 link，例如 `l6`；
3. 两个夹爪手指使用 `prismatic` 或 `revolute` joint；
4. 先在 RViz2 中用 GUI 验证开合；
5. 再根据真实夹爪驱动方式配置控制器。

示意：

```text
l6
 └── tool0 (fixed)
      └── gripper_base (fixed)
           ├── left_finger_joint  (prismatic)
           └── right_finger_joint (prismatic)
```

### 10.2 MoveIt 2

在进入 MoveIt 2 前，至少要完成：

- 真实的关节上下限；
- 可靠的 `base_link` 和末端 `tool0`；
- 合理的 collision；
- 正确关节轴和零位；
- SRDF、规划组、控制器配置。

### 10.3 Gazebo / 物理仿真

在进入 Gazebo 前，至少要完成：

- 每个 link 合理的质量、质心、惯性矩；
- 合理且简化的 collision 模型；
- 关节阻尼、摩擦、传动与控制器；
- 仿真插件和 `ros2_control` 配置。

### 10.4 真实机械臂控制

真实控制之前必须具备：

- 厂家官方 ROS 2 驱动或 SDK；
- 正确 IP/串口、急停、使能、速度限制；
- 正确型号和固件兼容性；
- 厂家确认的关节限位、负载、TCP、工具坐标；
- 空载、低速、隔离区域的安全测试。

> RViz2 发布的 `/joint_states` 只是“显示状态数据”；它**不会**自动让越疆机械臂实体运动。

---

## 11. 最终交付检查清单

把任意 SolidWorks 导出模型交付为 ROS 2 Foxy 可显示包前，逐项打勾。

### 文件和命名

- [ ] 包目录名仅包含小写字母、数字、下划线。
- [ ] `package.xml` 的 `<name>` 与包目录名一致。
- [ ] `CMakeLists.txt` 的 `project(...)` 与包名一致。
- [ ] launch 中 `get_package_share_directory(...)` 与包名一致。
- [ ] 所有 `package://包名/...` 使用同一个包名。
- [ ] `urdf/`、`meshes/`、`launch/` 都存在。
- [ ] 每个 URDF mesh 引用的文件实际存在，且大小写一致。

### URDF 结构

- [ ] 只有一个根 link，推荐叫 `base_link`。
- [ ] 根 link 已通过 fixed joint 连到原始底座 link。
- [ ] 每个 joint 的 parent/child link 都存在。
- [ ] 没有环路、没有一个 child 对应两个父 joint。
- [ ] 每个活动关节有正确的 type、axis、limit。
- [ ] 不再有用于活动关节的 `lower="0" upper="0"`（除非它确实永远锁死）。
- [ ] `visual` 网格可用；后续规划/仿真还检查 `collision` 和 `inertial`。
- [ ] 单位一致：位置为米、角度为弧度、惯量单位正确。

### ROS 2 构建和显示

- [ ] 已 `source /opt/ros/foxy/setup.bash`。
- [ ] `colcon build --packages-select 包名` 无错误。
- [ ] 已执行 `source install/setup.bash`。
- [ ] `ros2 launch 包名 display.launch.py` 能启动。
- [ ] RViz2 的 Fixed Frame 设为 `base_link`。
- [ ] RViz2 `RobotModel` 状态为 Ok。
- [ ] `joint_state_publisher_gui` 中活动关节滑块能改变模型姿态。
- [ ] `ros2 topic echo /joint_states --once` 能得到关节状态。
- [ ] `ros2 run tf2_ros tf2_echo base_link 末端link` 能得到变换。

---

## 一页式可复制流程

将 `your_robot_description`、`your_robot.urdf` 替换为自己的实际名称：

```bash
# 1) 加载 Foxy
source /opt/ros/foxy/setup.bash

# 2) 确认包位于工作空间 src 中
cd ~/Desktop/dev_ws
ls src/your_robot_description

# 3) 构建
colcon build --symlink-install --packages-select your_robot_description

# 4) 让当前终端识别新包
source install/setup.bash

# 5) 启动显示
ros2 launch your_robot_description display.launch.py
```

若启动后模型不显示，按以下顺序检查，效率最高：

```text
1. ROS 2 包名是否全部一致？
2. 每一个 package:// 路径是否指向存在的 mesh？
3. CMakeLists.txt 是否安装了 urdf、meshes、launch？
4. Fixed Frame 是否为 base_link？
5. base_link 是否经 fixed joint 连到原模型的根 link？
6. 活动 joint 是否有非零 lower/upper 限位？
7. build 后是否 source 了 install/setup.bash？
```

---

## 结语：建议的工作习惯

1. **先让模型在 RViz2 完整显示，再做控制。**
2. 每次只改一个问题：先路径，再 TF，再关节限位，再坐标方向。
3. 所有“临时为了能动而写的参数”都标注为测试值，特别是 joint limit、质量和惯量。
4. 为每个模型保留：原始 SolidWorks 导出物、可显示的 ROS 2 description 包、修改记录。
5. 模型一旦计划用于 MoveIt / 仿真 / 实机，重新核验关节限位、质量、惯量、碰撞体和工具坐标，不能沿用显示阶段的假设值。
