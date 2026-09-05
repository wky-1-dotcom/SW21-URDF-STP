# SW2URDF 导出包转 ROS 2 Foxy 通用转换模板（公开版）

> 适用对象：使用 SolidWorks SW2URDF 导出的机械臂、夹爪或末端执行器模型。  
> 本文示例环境：Ubuntu 20.04 + ROS 2 Foxy。  
> 目标：在没有 AI 辅助时，按顺序把 ROS 1/Catkin 风格导出包整理成可由 ROS 2、robot_state_publisher 和 RViz2 读取的 description 包。  
> 示例包名：`dobot_cr7_gripper_description`。公开使用时必须替换为自己的名称。

---

## 0. 使用前先理解这三个结论

### 0.1 不是所有 SolidWorks 导出的 URDF 都有一个“ROS 2 版本”

URDF 中的 link、joint、visual、collision、inertial 等核心 XML 语法在 ROS 1 和 ROS 2 中基本相同。通常需要转换的是 URDF 外面的功能包：

| 检查项 | SW2URDF/ROS 1 常见输出 | ROS 2 Foxy 要求 |
|---|---|---|
| package.xml | catkin、roslaunch、rviz | ament_cmake、launch、launch_ros、rviz2 |
| CMakeLists.txt | catkin_package() | ament_package() |
| 启动文件 | display.launch（ROS 1 XML） | display.launch.py（ROS 2 Python） |
| 包名 | 可能有中文、空格、加号 | 推荐小写英文、数字、下划线 |
| mesh URI | package://旧包名/meshes/... | package://新包名/meshes/... |
| 构建命令 | catkin_make | colcon build |

是否要转换取决于 SW2URDF 的输出，不取决于 SolidWorks 2021、2022 或其他版本。只要仍然是 Catkin 和 ROS 1 launch，就按本文转换；如果已经是 ament_cmake 和 ROS 2 Python launch，只做检查，不重复转换。

### 0.2 格式正确不代表机械结构正确

本模板可以规范：

- ROS 2 包结构；
- 文件名、包名和资源路径；
- package.xml、CMakeLists.txt、launch 和 RViz2 配置；
- 重名、空关节名、明显锁死的显示限位。

本模板不能凭空确定：

- 真实关节限位、速度和力矩；
- 正确的 joint origin 和 axis；
- 丝杠导程；
- 闭环连杆的非线性联动；
- 实机碰撞与安全参数。

这些内容必须来自 CAD 几何、厂家资料、控制器参数或实测。

### 0.3 全文统一占位符

在开始前确定：

| 占位符 | 含义 | 示例 |
|---|---|---|
| YOUR_PACKAGE_NAME | ROS 2 包名 | dobot_cr7_gripper_description |
| YOUR_ROBOT_NAME | robot 标签名称 | dobot_cr7_gripper |
| YOUR_URDF_FILE | 不含扩展名的 URDF 文件名 | dobot_cr7_gripper |
| YOUR_ROOT_LINK | 原导出 URDF 的根 link | b0 |

命名统一规则：

- 包名使用小写英文字母、数字和下划线；
- 包名以英文字母开头，description 包以 _description 结尾；
- 不使用中文、空格、加号；
- link 和 joint 名必须各自唯一；
- 为兼容更多工具，link 和 joint 名也建议以英文字母开头。

示例替换：

~~~text
YOUR_PACKAGE_NAME → dobot_cr7_gripper_v9_description
YOUR_ROBOT_NAME   → dobot_cr7_gripper_v9
YOUR_URDF_FILE    → dobot_cr7_gripper_v9
YOUR_ROOT_LINK    → b0
~~~

---

# 公开模板的固定执行顺序

## A. 先增加文件

前提是已经备份原导出目录，并创建新的 ROS 2 包：

~~~bash
source /opt/ros/foxy/setup.bash
mkdir -p ~/Desktop/dev_ws/src
cd ~/Desktop/dev_ws/src

ros2 pkg create \
  --build-type ament_cmake \
  YOUR_PACKAGE_NAME

cd YOUR_PACKAGE_NAME
mkdir -p config launch meshes rviz urdf

cp /原始导出目录/meshes/* meshes/
cp /原始导出目录/urdf/原始文件名.urdf \
  urdf/YOUR_URDF_FILE.urdf
~~~

在新 ROS 2 包中先增加：

~~~text
launch/display.launch.py
rviz/display.rviz
config/joint_names.yaml
README.md
~~~

然后再按下面顺序修改 SW2URDF 原文件：

~~~text
1. package.xml
2. CMakeLists.txt
3. config/旧 joint_names 文件
4. launch/旧 ROS 1 文件
5. meshes/网格与文件名
6. urdf/机器人 URDF（严格从顶部向下检查）
~~~

## A1. 新增 launch/display.launch.py

完整内容如下，替换 YOUR_PACKAGE_NAME 和 YOUR_URDF_FILE：

~~~python
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(
        get_package_share_directory("YOUR_PACKAGE_NAME")
    )
    urdf_path = package_share / "urdf" / "YOUR_URDF_FILE.urdf"
    rviz_path = package_share / "rviz" / "display.rviz"
    robot_description = urdf_path.read_text(encoding="utf-8")

    return LaunchDescription(
        [
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="joint_state_publisher_gui",
                output="screen",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=["-d", str(rviz_path)],
                parameters=[{"robot_description": robot_description}],
            ),
        ]
    )
~~~

## A2. 新增 rviz/display.rviz

完整通用配置：

~~~yaml
Panels:
  - Class: rviz_common/Displays
    Name: Displays
Visualization Manager:
  Class: ""
  Displays:
    - Alpha: 0.5
      Cell Size: 1
      Class: rviz_default_plugins/Grid
      Color: 160; 160; 164
      Enabled: true
      Name: Grid
      Plane: XY
      Plane Cell Count: 10
    - Alpha: 1
      Class: rviz_default_plugins/RobotModel
      Collision Enabled: false
      Description Source: Topic
      Description Topic:
        Depth: 5
        Durability Policy: Transient Local
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /robot_description
      Enabled: true
      Name: RobotModel
      Robot Description: robot_description
      Visual Enabled: true
    - Class: rviz_default_plugins/TF
      Enabled: true
      Frame Timeout: 15
      Marker Scale: 0.15
      Name: TF
      Show Arrows: true
      Show Axes: true
      Show Names: false
  Enabled: true
  Global Options:
    Background Color: 48; 48; 48
    Fixed Frame: base_link
    Frame Rate: 30
  Name: root
  Tools:
    - Class: rviz_default_plugins/Interact
    - Class: rviz_default_plugins/MoveCamera
    - Class: rviz_default_plugins/Select
  Value: true
  Views:
    Current:
      Class: rviz_default_plugins/Orbit
      Distance: 2
      Focal Point:
        X: 0
        Y: 0
        Z: 0.4
      Name: Current View
      Pitch: 0.45
      Target Frame: base_link
      Yaw: 0.75
Window Geometry:
  Height: 900
  Width: 1400
~~~

若没有增加 base_link，必须把 Fixed Frame 和 Target Frame 改成实际根 link；但公开模板推荐增加 base_link。

## A3. 新增 config/joint_names.yaml

示例：

~~~yaml
controller_joint_names:
  - joint_1
  - joint_2
  - joint_3
  - joint_4
  - joint_5
  - joint_6
  - gripper_joint
~~~

替换为实际主动关节。不要填写：

- 空字符串；
- 重复 joint；
- fixed joint；
- 已由 mimic 控制的从动 joint；
- URDF 中不存在的 joint。

这个文件只是名称清单，不是 ros2_control 控制器配置。

## A4. 新增 README.md

公开包至少写清构建方法、来源和参数性质：

~~~text
# YOUR_PACKAGE_NAME

ROS 2 description package converted from a SolidWorks SW2URDF export.

Build:
  source /opt/ros/foxy/setup.bash
  cd ~/Desktop/dev_ws
  colcon build --symlink-install --packages-select YOUR_PACKAGE_NAME
  source install/setup.bash

Display:
  ros2 launch YOUR_PACKAGE_NAME display.launch.py

Temporary visualization limits are not approved for simulation or real hardware.
~~~

完成 A1 至 A4 后，再进入下文，依次修改 package.xml、CMakeLists.txt、config、launch、meshes 和 URDF。

---

## 1. 转换流程总览

```text
SolidWorks 检查模型和关节
        ↓
SW2URDF 导出 URDF、STL 和 ROS 1 包
        ↓
完整备份原始导出目录
        ↓
创建合法的 ROS 2 description 包
        ↓
复制 URDF 和 meshes
        ↓
修改包名、mesh URI、根坐标系和关节限位
        ↓
编写 package.xml、CMakeLists.txt 和 ROS 2 launch
        ↓
colcon build
        ↓
robot_state_publisher + joint_state_publisher_gui + RViz2
        ↓
检查模型、TF、关节方向、零位和夹爪联动
```

---

## 2. SolidWorks 导出前检查

### 2.1 使用模型副本

不要直接在唯一的原始装配体上修改。复制顶层装配体及其引用零件，所有简化、解散子装配体和坐标系修改都在副本中完成。

### 2.2 处理 STEP 和虚拟零部件

如果模型来自 STEP/STP：

1. 关闭 SolidWorks 的 3D Interconnect 后重新导入，或者断开现有 3D Interconnect 链接。
2. 将顶层装配体保存为 `.SLDASM`。
3. 将虚拟零部件保存为外部 `.SLDPRT` 或 `.SLDASM` 文件。
4. 确认组件名称不再包含方括号或 `^顶层装配体名`。
5. 将轻化组件设为“已解析”。

### 2.3 正确划分 link

一个 link 只能包含运动时彼此刚性不变的零件。六轴机械臂通常为：

```text
b0 --j1--> l1 --j2--> l2 --j3--> l3
   --j4--> l4 --j5--> l5 --j6--> l6
```

注意：

- 不要把整个机器人装配体分配给基座 link。
- 同一个零件不能同时分配给两个 link。
- 子装配体导出失败时，应选择内部实际叶级零件，或在副本中解散子装配体。
- 每个 link 都应具有有效实体、质量、质心和惯性。

### 2.4 正确定义 joint

每个旋转关节必须满足：

- 原点位于真实旋转中心。
- Z 轴与真实旋转轴重合。
- 轴正方向遵循右手定则。
- Parent 和 Child 关系正确。
- 机械零位与 URDF 的零位一致。
- Lower/Upper Limit 合理。

不要通过随意改变 STL 姿态来补偿关节轴错误。

### 2.5 夹爪闭环机构特别注意

URDF 原生要求机器人结构是一棵树，不能直接描述一个 link 同时通过两个关节连接到两个父 link 的闭环机构。

四连杆夹爪、平行夹爪等机构在 SolidWorks 中使用的同心、重合、齿轮和连杆配合，不会自动成为 URDF 约束。常见处理方式：

1. 为 RViz2/MoveIt 2 简化为左右两个夹指关节。
2. 对线性从动关系使用 `<mimic>`。
3. 对非线性四连杆关系编写节点计算并发布从动关节角度。
4. 需要真实闭环动力学时使用 SDF、Gazebo 插件或其他闭环约束方案。

---

## 3. 使用 SW2URDF 导出

在 SolidWorks 中完成 link 和 joint 配置后：

1. 新建一个空的英文路径导出目录。
2. 选择 `Export URDF and Meshes...`。
3. 不要只选择 `Export URDF Only...`，否则 STL 不会重新生成。
4. 导出期间关闭 MeshLab、3D 查看器和资源管理器预览窗格，避免 STL 被占用。

典型导出结果：

```text
solidworks_export/
├── config/
├── launch/
├── meshes/
│   ├── b0.STL
│   ├── l1.STL
│   └── ...
├── urdf/
│   └── robot.urdf
├── CMakeLists.txt
└── package.xml
```

SolidWorks 导出的 `package.xml`、`CMakeLists.txt` 和 `.launch` 通常是 ROS 1 Catkin 格式，不能原样作为 ROS 2 包使用。

---

## 4. 导出后先验证 STL 和 URDF

转换前先确认源文件本身有效：

1. 单独打开每个 STL，确认不是空网格。
2. 检查各 STL 的方向和尺度。
3. 检查文件名大小写，例如 `l1.STL` 与 `l1.stl` 在 Linux 中不同。
4. 检查 URDF 是否包含所有 link 和 joint。
5. 检查每个 `<mesh filename="...">` 是否指向实际文件。
6. 检查零位姿态下各销轴、法兰和连杆是否对齐。

如果网页查看器只显示基座，而关节树完整，通常是子 link 的 STL 为空、路径错误或单位错误，不是 ROS 2 转换问题。

---

## 5. 备份原始 SolidWorks 导出结果

在 Ubuntu 中执行：

```bash
cp -a solidworks_export solidworks_export_backup
```

推荐保留：

- 原始 URDF。
- 原始 ROS 1 配置文件。
- STL 网格。
- SW2URDF 导出日志和 CSV。
- SolidWorks 模型副本。

不要直接把唯一的原始导出目录改成 ROS 2 包。

---

## 6. 创建 ROS 2 description 包

### 6.1 包名规则

ROS 2 包名建议：

- 只使用小写英文字母、数字和下划线。
- 不能包含空格、加号、中文或连字符。
- description 包通常以 `_description` 结尾。

本文使用：

```text
dobot_cr7_gripper_description
```

### 6.2 创建包

```bash
source /opt/ros/foxy/setup.bash

mkdir -p ~/Desktop/dev_ws/src
cd ~/Desktop/dev_ws/src

ros2 pkg create \
  --build-type ament_cmake \
  dobot_cr7_gripper_description
```

创建资源目录：

```bash
cd ~/Desktop/dev_ws/src/dobot_cr7_gripper_description
mkdir -p config launch meshes rviz urdf
```

复制网格和 URDF：

```bash
cp /原始导出目录/meshes/* meshes/
cp /原始导出目录/urdf/原始文件名.urdf \
  urdf/dobot_cr7_gripper.urdf
```

最终结构：

```text
dobot_cr7_gripper_description/
├── CMakeLists.txt
├── package.xml
├── README.md
├── config/
│   └── joint_names.yaml
├── launch/
│   └── display.launch.py
├── meshes/
│   └── *.STL
├── rviz/
│   └── display.rviz
└── urdf/
    └── dobot_cr7_gripper.urdf
```

---

## 7. 修改 URDF

### 7.1 修改机器人名称

原始名称可能包含中文、空格或加号：

```xml
<robot name="机械臂+末端执行器-5">
```

改为：

```xml
<robot name="YOUR_ROBOT_NAME">
```

### 7.2 修改所有 mesh URI

原始：

```xml
<mesh filename="package://机械臂+末端执行器-5/meshes/l1.STL" />
```

改为：

```xml
<mesh filename="package://YOUR_PACKAGE_NAME/meshes/l1.STL" />
```

`visual` 和 `collision` 中的全部 mesh 路径都要修改。

### 7.3 增加 base_link

如果原始根 link 是 `YOUR_ROOT_LINK`，可在 `<robot>` 内增加：

```xml
<link name="base_link" />

<joint name="base_link_to_root" type="fixed">
  <origin xyz="0 0 0" rpy="0 0 0" />
  <parent link="base_link" />
  <child link="YOUR_ROOT_LINK" />
</joint>
```

这样 RViz2 的 Fixed Frame 可以统一设置为：

```text
base_link
```

### 7.4 修正被锁死的关节限位

SW2URDF 可能导出：

```xml
<limit lower="0" upper="0" effort="0" velocity="0" />
```

这会使 Joint State Publisher GUI 无法移动关节。仅用于 RViz2 显示测试时，可临时设置：

```xml
<limit
  lower="-3.14159265359"
  upper="3.14159265359"
  effort="10.0"
  velocity="1.0" />
```

这些数值不是厂家安全参数。用于 MoveIt 2、Gazebo、`ros2_control` 或真实机器人以前，必须替换为厂家确认的范围、速度和力矩限制。

### 7.5 配置 mimic 关节

只有从动关系确实为线性时才能使用：

```xml
<mimic joint="j7" multiplier="-1.0" offset="0.0" />
```

计算关系：

```text
q从动 = multiplier × q主动 + offset
```

判断方法：

1. 暂时删除从动关节的 `<mimic>`。
2. 在多个主动关节角度下手动调节从动关节，使销孔重新对齐。
3. 记录主动角和从动角。
4. 若比例和偏置在整个范围内基本不变，才使用 mimic。
5. 若比例随位置变化，则属于非线性闭环，不能只靠 mimic。

不要因为“不穿模”就认为关节关系正确，还必须检查销孔、轴心和连杆连接点是否始终重合。

---

### 7.6 按 URDF 顶部到底部检查每个 link

每个 link 通常按下面顺序出现：

~~~xml
<link name="link_1">
  <inertial>...</inertial>
  <visual>...</visual>
  <collision>...</collision>
</link>
~~~

逐个检查：

- name 唯一；
- inertial 的质量和惯性为有限数值；
- visual mesh 能显示；
- collision mesh 路径也已修改；
- link 内只能包含运动时保持刚性的零件。

真实原始名称示例：

~~~xml
<link name="2-j-2">
~~~

为提高跨工具兼容性，可改为：

~~~xml
<link name="gripper_left_linkage">
~~~

同时修改所有对应引用：

~~~xml
<child link="gripper_left_linkage" />
<parent link="gripper_left_linkage" />
~~~

只改 link 标识符时不需要改 STL 文件名；只有实际重命名 STL 时才同步改 mesh filename。

### 7.7 按出现顺序检查每个 joint name

真实错误示例：

~~~xml
<joint name="2j" type="revolute">
  ...
</joint>

<joint name="2j" type="revolute">
  ...
</joint>
~~~

同名 joint 不可用，应改为：

~~~xml
<joint name="gripper_left_linkage_joint" type="revolute">
  ...
</joint>

<joint name="gripper_right_linkage_joint" type="revolute">
  ...
</joint>
~~~

改名后同步更新：

- mimic 的 joint 属性；
- config/joint_names.yaml；
- 后续 ros2_control 控制器；
- MoveIt 2 配置；
- 自己编写的控制程序。

### 7.8 检查 joint 的 parent 和 child

原始或修改后都必须满足：

~~~xml
<joint name="joint_1" type="revolute">
  <parent link="base_link" />
  <child link="link_1" />
</joint>
~~~

规则：

- parent 和 child 必须引用已经声明的 link；
- parent 与 child 不能相同；
- 一个普通 URDF child link 只能有一个父 joint；
- 整个 URDF 只能有一个根；
- 不能形成环。

SolidWorks 中的闭环配合不能原样写成树形 URDF。需要断开一处、使用简化模型，或在后续仿真层加入闭环约束。

### 7.9 检查 origin、axis 和 joint type

典型旋转关节：

~~~xml
<joint name="elbow_joint" type="revolute">
  <origin xyz="0 0 0.2" rpy="0 0 0" />
  <parent link="upper_arm" />
  <child link="forearm" />
  <axis xyz="0 0 1" />
  <limit lower="-1.57" upper="1.57"
         effort="10.0" velocity="1.0" />
</joint>
~~~

典型直线关节：

~~~xml
<joint name="gripper_slider_joint" type="prismatic">
  <origin xyz="0 0 0" rpy="0 0 0" />
  <parent link="gripper_base" />
  <child link="gripper_slider" />
  <axis xyz="0 0 1" />
  <limit lower="0.0" upper="0.02"
         effort="100.0" velocity="0.05" />
</joint>
~~~

单位：

| 内容 | 单位 |
|---|---|
| origin xyz | m |
| origin rpy | rad |
| revolute lower/upper | rad |
| prismatic lower/upper | m |

检查依据：

- revolute 原点必须位于真实轴心，axis 与真实转轴重合；
- prismatic axis 必须平行于真实移动方向；
- axis 在 joint 局部坐标系中表达，不一定等于世界坐标方向；
- 零位不正确时，应回到 SolidWorks 检查坐标系和 link 分组；
- 不要通过移动 mesh 来掩盖错误 joint origin。

### 7.10 丝杠和不同 joint type 的 mimic

原始错误示例：

~~~xml
<joint name="jlink" type="prismatic">
  ...
  <mimic joint="j6" multiplier="1" offset="0" />
</joint>
~~~

如果 j6 是机械臂腕部 revolute，而 jlink 是夹爪滑块 prismatic，这通常是错误关系。不能默认 1 rad 等于 1 m。

丝杠的基础关系为：

~~~text
螺母位移 x = 丝杠导程 lead / (2π) × 丝杠转角 theta
~~~

没有可靠导程和机构方程时，修改为暂时独立关节：

~~~xml
<joint name="gripper_slider_joint" type="prismatic">
  ...
  <limit lower="-0.02" upper="0.02"
         effort="100.0" velocity="0.05" />
</joint>
~~~

这里的范围仍只是显示示例。确认真实数据后，再添加正确 mimic、计算节点或仿真约束。

### 7.11 检查 inertial

原始结构一般可保留：

~~~xml
<inertial>
  <origin xyz="0 0 0" rpy="0 0 0" />
  <mass value="1.0" />
  <inertia
    ixx="0.01" ixy="0" ixz="0"
    iyy="0.01" iyz="0" izz="0.01" />
</inertial>
~~~

RViz2 显示不依赖真实质量，但 Gazebo/Isaac Sim 动力学依赖。用于仿真前检查：

- mass 大于 0；
- ixx、iyy、izz 大于 0；
- 惯性矩阵物理有效；
- 质量改变时重新计算质心和惯性；
- 不能把估算值写成厂家真实数据。

### 7.12 可选增加 tool0 和 tcp

只在 RViz2 显示时不是必需，但 MoveIt 2 和实机笛卡尔控制通常需要：

~~~xml
<link name="tool0" />
<joint name="flange_to_tool0" type="fixed">
  <parent link="flange" />
  <child link="tool0" />
  <origin xyz="0 0 0" rpy="0 0 0" />
</joint>

<link name="tcp" />
<joint name="tool0_to_tcp" type="fixed">
  <parent link="tool0" />
  <child link="tcp" />
  <origin xyz="0 0 0.12" rpy="0 0 0" />
</joint>
~~~

0.12 m 只是格式示例，必须替换为真实工具尺寸。

### 7.13 RViz2 转换阶段不增加仿真控制内容

仅为了在 RViz2 显示时，不需要先写：

- gazebo 标签；
- transmission；
- ros2_control；
- MoveIt 2 SRDF；
- 实机通信配置。

这些属于后续仿真、规划和控制，不能通过复制通用数值完成。

## 8. 编写 package.xml

SW2URDF 原始 ROS 1 示例：

~~~xml
<package format="2">
  <name>机械臂+末端执行器-9</name>
  <version>1.0.0</version>
  <description>URDF Description package</description>
  <maintainer email="TODO@email.com">TODO</maintainer>
  <license>BSD</license>
  <buildtool_depend>catkin</buildtool_depend>
  <depend>roslaunch</depend>
  <depend>robot_state_publisher</depend>
  <depend>rviz</depend>
  <depend>joint_state_publisher_gui</depend>
</package>
~~~

不能只把 catkin 单词删除。应使用下面的 ROS 2 内容完整替换，并统一替换包名、描述、维护者和许可证：

```xml
<?xml version="1.0"?>
<package format="3">
  <name>dobot_cr7_gripper_description</name>
  <version>1.0.0</version>
  <description>ROS 2 description package for a DOBOT CR7 with a gripper.</description>
  <maintainer email="maintainer@example.com">Maintainer</maintainer>
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

要点：

- `catkin` 必须改为 `ament_cmake`。
- ROS 1 的 `roslaunch`、`rviz` 不能直接照搬。
- RViz2 包名是 `rviz2`。

---

## 9. 编写 CMakeLists.txt

SW2URDF 原始 ROS 1 示例：

~~~cmake
cmake_minimum_required(VERSION 2.8.3)
project(机械臂+末端执行器-9)

find_package(catkin REQUIRED)
catkin_package()

foreach(dir config launch meshes urdf)
  install(DIRECTORY ${dir}/
    DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/${dir})
endforeach(dir)
~~~

上面的 Catkin 宏不能在 ament_cmake 包中继续使用。用下面内容完整替换：

```cmake
cmake_minimum_required(VERSION 3.5)
project(dobot_cr7_gripper_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch meshes rviz urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
```

必须安装 `meshes` 和 `urdf`，否则编译后 `package://` URI 找不到模型。

---

## 10. 编写 ROS 2 启动文件

SW2URDF 原始文件通常是 ROS 1 XML：

~~~xml
<launch>
  <param
    name="robot_description"
    textfile="$(find 机械臂+末端执行器-9)/urdf/机械臂+末端执行器-9.urdf" />
  <node
    pkg="joint_state_publisher_gui"
    type="joint_state_publisher_gui" />
  <node
    pkg="robot_state_publisher"
    type="robot_state_publisher" />
  <node pkg="rviz" type="rviz" />
</launch>
~~~

不能通过把后缀改成 .py 来转换。应新建 ROS 2 Python launch；完整模板已在 A1 给出，下面保留同一内容作为详细说明。

创建：

```text
launch/display.launch.py
```

内容：

```python
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(
        get_package_share_directory("dobot_cr7_gripper_description")
    )
    urdf_path = package_share / "urdf" / "dobot_cr7_gripper.urdf"
    rviz_path = package_share / "rviz" / "display.rviz"
    robot_description = urdf_path.read_text(encoding="utf-8")

    return LaunchDescription(
        [
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="joint_state_publisher_gui",
                output="screen",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                arguments=["-d", str(rviz_path)],
            ),
        ]
    )
```

三个节点的作用：

| 节点 | 作用 |
|---|---|
| `joint_state_publisher_gui` | 显示关节角度滑块并发布 `/joint_states` |
| `robot_state_publisher` | 根据 URDF 和关节角计算并发布 TF |
| `rviz2` | 显示 RobotModel、TF 和 Grid |

---

## 11. 创建关节列表

SW2URDF 原始错误示例：

~~~yaml
controller_joint_names: ['', 'j1', 'j2', '2j', '2j', ]
~~~

其中空字符串、重复名称以及无效名称都必须删除或修正。

`config/joint_names.yaml` 示例：

```yaml
controller_joint_names: [j1, j2, j3, j4, j5, j6, j7]
```

注意：

- 不要包含空字符串。
- mimic 从动关节通常不作为独立控制关节列出。
- 该文件不能代替真实的 `ros2_control` 控制器配置。

---

## 12. 创建 RViz2 配置

最简单的方法：

1. 先启动 RViz2。
2. 将 Fixed Frame 设置为 `base_link`。
3. 添加 `RobotModel`。
4. 添加 `TF`。
5. 保留或添加 `Grid`。
6. 选择 `File -> Save Config As`。
7. 保存为包内的 `rviz/display.rviz`。

若 RobotModel 支持 Description Source：

- ROS 2 新版本通常选择 `Topic` 和 `/robot_description`。
- 部分 Foxy 配置显示为 `Robot Description: robot_description`。

---

## 13. 安装 ROS 2 显示组件

Ubuntu 20.04 + Foxy：

```bash
sudo apt update
sudo apt install \
  ros-foxy-joint-state-publisher-gui \
  ros-foxy-robot-state-publisher \
  ros-foxy-rviz2
```

如使用其他 ROS 2 发行版，将 `foxy` 替换为实际的 `$ROS_DISTRO`。

---

## 14. 编译 ROS 2 包

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/dev_ws

colcon build \
  --symlink-install \
  --packages-select dobot_cr7_gripper_description

source install/setup.bash
```

每次打开新终端，都需要重新执行：

```bash
source /opt/ros/foxy/setup.bash
source ~/Desktop/dev_ws/install/setup.bash
```

确认 ROS 2 找到包：

```bash
ros2 pkg prefix dobot_cr7_gripper_description
```

---

## 15. 启动 RViz2

```bash
ros2 launch dobot_cr7_gripper_description display.launch.py
```

正常情况下会出现：

- RViz2 主窗口。
- Joint State Publisher 独立滑块窗口。
- 终端中的 robot_state_publisher 日志。

Joint State Publisher 不是 RViz2 内部面板。如果没有看到，先按 `Alt+Tab` 检查是否被 RViz2 遮挡。

手动启动滑块窗口：

```bash
ros2 run joint_state_publisher_gui joint_state_publisher_gui
```

检查节点：

```bash
ros2 node list
```

应看到类似：

```text
/joint_state_publisher_gui
/robot_state_publisher
/rviz2
```

---

## 16. 验证安装后的资源

查看安装目录：

```bash
PKG_PREFIX=$(ros2 pkg prefix dobot_cr7_gripper_description)

ls "$PKG_PREFIX/share/dobot_cr7_gripper_description/urdf"
ls "$PKG_PREFIX/share/dobot_cr7_gripper_description/meshes"
ls "$PKG_PREFIX/share/dobot_cr7_gripper_description/launch"
```

检查 URDF XML：

```bash
xmllint --noout \
  ~/Desktop/dev_ws/src/dobot_cr7_gripper_description/urdf/dobot_cr7_gripper.urdf
```

如已安装 `check_urdf`：

```bash
check_urdf \
  ~/Desktop/dev_ws/src/dobot_cr7_gripper_description/urdf/dobot_cr7_gripper.urdf
```

检查 TF：

```bash
ros2 run tf2_tools view_frames.py
```

---

## 17. RViz2 验收项目

- [ ] Fixed Frame 为 `base_link`。
- [ ] RobotModel 状态为 `Ok`。
- [ ] 所有机械臂和夹爪 STL 均显示。
- [ ] TF 树只有一个根坐标系。
- [ ] Joint State Publisher 显示所有主动关节。
- [ ] `j1` 到 `j6` 的旋转中心正确。
- [ ] 关节正方向符合设计。
- [ ] 零位姿态符合 SolidWorks 装配体。
- [ ] 夹爪运动时销孔和轴心保持对齐。
- [ ] mimic 关节没有独立滑块。
- [ ] 没有使用显示测试限位控制真实机械臂。

---

## 18. 常见故障排查

### 18.1 RViz2 只有 Grid，没有机器人

检查：

- 是否添加 RobotModel。
- Robot Description 是否正确。
- launch 是否启动 robot_state_publisher。
- URDF XML 是否解析失败。

### 18.2 有 TF 但没有实体模型

通常是 mesh 路径问题：

```bash
ls "$(ros2 pkg prefix dobot_cr7_gripper_description)/share/dobot_cr7_gripper_description/meshes"
```

同时检查 `package://` 后面的包名和 STL 文件大小写。

### 18.3 没有关节滑块窗口

```bash
ros2 run joint_state_publisher_gui joint_state_publisher_gui
```

若提示找不到包：

```bash
sudo apt install ros-foxy-joint-state-publisher-gui
```

### 18.4 滑块存在但关节不动

检查关节是否仍为：

```xml
<limit lower="0" upper="0" effort="0" velocity="0" />
```

还要检查 joint type 是否误设为 `fixed`。

### 18.5 关节绕错误位置旋转

原因通常是 SolidWorks 中的关节坐标系原点没有放在真实轴心。应回到 SW2URDF 的 Joint 配置修正 origin，而不是移动 STL 补偿。

### 18.6 旋转方向相反

优先检查：

- `<axis xyz="...">` 的方向。
- 关节坐标系 Z 轴方向。
- mimic 的 `multiplier` 正负号。

### 18.7 夹爪移动后销孔分离

如果零位时重合、移动后分离：

- STL 和零位通常正确。
- 问题集中在闭环机构和从动角关系。
- 暂时删除 mimic，独立调整各从动关节并记录角度。
- 只有关系为固定比例时才能使用 mimic。
- 非线性关系需要计算节点、查表插值或简化模型。

### 18.8 修改源码后效果没有变化

重新编译并加载工作空间：

```bash
cd ~/Desktop/dev_ws

colcon build \
  --symlink-install \
  --packages-select dobot_cr7_gripper_description \
  --cmake-clean-cache

source install/setup.bash
ros2 launch dobot_cr7_gripper_description display.launch.py
```

确认当前加载的是正确包：

```bash
ros2 pkg prefix dobot_cr7_gripper_description
```

---

## 18A. 真实 SW2URDF 导出错误案例

下面的问题来自本目录“机械臂+末端执行器-9”的实际 SW2URDF 输出，用于说明为什么不能只改包名。

| 原始内容 | 问题依据 | 处理原则 |
|---|---|---|
| 包名为 机械臂+末端执行器-9 | 含中文和加号，不适合作为通用 ROS 2 包名及 package URI | 改成小写英文下划线名称 |
| package.xml 使用 catkin | 属于 ROS 1 构建系统 | 完整替换为 ament_cmake |
| display.launch 使用 ROS 1 XML | Foxy 使用 ROS 2 launch API | 新建 display.launch.py |
| mesh URI 指向旧中文包名 | 安装后无法从新包解析资源 | visual 和 collision 全部替换 |
| joint_names 第一项为空字符串 | 空字符串不是有效 joint | 删除 |
| 两个 joint 都名为 2j | joint 名必须唯一 | 分别改成左右唯一名称 |
| 多个 joint 的 lower 和 upper 都为 0 | 关节被锁死，GUI 无有效范围 | 查真实限位；仅显示时可使用明确标注的临时范围 |
| effort 和 velocity 都为 0 | 不能作为有效仿真或控制参数 | 查厂家参数；显示测试值必须明确标注 |
| prismatic 的 jlink mimic revolute 的 j6，multiplier 为 1 | 腕关节转角不应直接等值变成夹爪位移，rad 与 m 也不同 | 删除错误 mimic，根据丝杠导程重建 |
| 多个夹爪关节 mimic j6 | 夹爪会错误跟随机械臂腕部 | 指向真正主动关节，或先独立检查 |
| 没有 base_link | Fixed Frame 和后续集成不统一 | 增加固定根坐标系 |

丝杠关系示例：

~~~text
螺母位移 x = 丝杠导程 lead / (2π) × 丝杠转角 theta
~~~

如果从滑块位移到连杆角度是非线性的，不能仅用一个固定 mimic multiplier。应使用机构方程、查表插值、自定义 joint-state 节点，或为 RViz2/MoveIt 2建立简化树模型。

这个案例说明转换必须分两层验收：

~~~text
第一层：ROS 2 包格式、文件和资源路径正确
第二层：机械零位、轴向、限位和联动关系正确
~~~

XML 能解析，只证明第一层的一部分通过。

---

## 19. 从 Windows 复制到 Ubuntu（可选）

如果 Ubuntu 运行在 WSL，可使用通用路径：

```bash
mkdir -p ~/Desktop/dev_ws/src

cp -a \
  /mnt/c/path/to/YOUR_PACKAGE_NAME \
  ~/Desktop/dev_ws/src/
```

如果是独立 Ubuntu 系统，通过 U 盘、局域网或共享目录复制整个 YOUR_PACKAGE_NAME 目录。不能只复制单个 URDF，因为模型还依赖 meshes、launch、rviz、package.xml 和 CMakeLists.txt。

复制后：

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/dev_ws

colcon build \
  --symlink-install \
  --packages-select YOUR_PACKAGE_NAME

source install/setup.bash
ros2 launch YOUR_PACKAGE_NAME display.launch.py
```

---

## 20. 安全说明

RViz2 和 Joint State Publisher GUI 只是在显示模型，不会自动控制真实机械臂。

接入 MoveIt 2、Gazebo、`ros2_control` 或真实硬件前，必须确认：

- 厂家关节范围。
- 速度和加速度限制。
- 力矩和载荷限制。
- 夹爪真实行程。
- TCP 和工具质量。
- 碰撞模型。
- 急停和安全边界。

临时的 `-π 到 +π`、`effort=10` 和 `velocity=1` 只用于模型显示测试，不能作为真实机器人安全参数。
