# cr7as_grasp_moveit_config（ROS 2 Humble / MoveIt 2）

这是 `cr7as_grasp` 的 MoveIt 2 配置包，负责规划、运动学、关节限制、轨迹控制器映射和 MoveIt RViz。它不重复保存机器人 STL；机器人 URDF 由同级的 `cr7as_grasp` 包提供。

## 规划坐标系

```text
world                         SRDF virtual joint 的父坐标系
└── base_link                 URDF 虚拟根
    └── b0                    规划基座
        └── ... -> l6
            └── gripper_base
                └── grasp_tcp  规划末端
```

- 规划组：`ARM`；
- base link：`b0`；
- tip link：`grasp_tcp`；
- 规划关节：`j1` 到 `j6`；
- 当前没有夹爪开合规划组。

`world` 只是在 SRDF 中连接规划场景的虚拟坐标系，不是 URDF 实体。`grasp_tcp` 是工具中心点坐标系，不代表夹爪指爪。

## 构建

```bash
source /opt/ros/humble/setup.bash
cd <仓库路径>/ROS2/Humble
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select \
  cr7as_grasp \
  cr7as_grasp_moveit_config
source install/setup.bash
```

## 与 Gazebo 联合启动

先在一个终端启动 Gazebo：

```bash
ros2 launch cr7as_grasp gazebo_control.launch.py
```

确认控制器：

```bash
ros2 control list_controllers -c /controller_manager
```

再分别启动 MoveIt 和 RViz：

```bash
ros2 launch cr7as_grasp_moveit_config move_group.launch.py
ros2 launch cr7as_grasp_moveit_config moveit_rviz.launch.py
```

Gazebo 链负责 `arm_controller`，MoveIt 配置使用 `moveit_manage_controllers=False`，轨迹动作目标为：

```text
/arm_controller/follow_joint_trajectory
```

MoveIt 和 RViz 必须使用 Gazebo 的 `/clock`，当前 launch 已设置 `use_sim_time=True`。不要同时启动旧的 `urdf_ros2_moveit_config` FakeSystem 配置。

## 诊断

```bash
ros2 topic echo /clock --once
ros2 topic echo /joint_states --once
ros2 action info /arm_controller/follow_joint_trajectory
ros2 param get /move_group use_sim_time
ros2 node list
```
