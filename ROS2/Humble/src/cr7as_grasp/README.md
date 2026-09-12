# cr7as_grasp（ROS 2 Humble）

这是 CR7AS 六轴机械臂的 ROS 2 Humble description 和 Gazebo Classic 控制包。它与同级的 `cr7as_grasp_moveit_config` 配置包一起组成当前仿真主线。

## 文件

- `urdf/cr7as_grasp.urdf`：RViz2 和 Joint State Publisher 使用的显示模型；
- `urdf/cr7as_grasp_gazebo.urdf`：包含 `ros2_control` 和 Gazebo Classic 插件的仿真模型；
- `meshes/`：机械臂和固定末端工具的 STL 网格；
- `launch/display.launch.py`：RViz2、Robot State Publisher 和关节滑块；
- `launch/gazebo_control.launch.py`：Gazebo Classic、机器人生成和六轴控制器；
- `config/gazebo_controllers.yaml`：`joint_state_broadcaster` 与 `arm_controller` 配置；
- `ROS2_Humble转换与故障排查.md`：本包从 SW2URDF 导出物转换时的项目特例和排错记录。

## 坐标系和末端模型

```text
base_link                         虚拟根坐标系
└── base_link_to_b0 [fixed]
    └── b0 -> l1 -> l2 -> l3 -> l4 -> l5 -> l6
        └── gripper_base_j [fixed]
            └── gripper_base       固定末端模型
                └── grasp_tcp_j [fixed]
                    └── grasp_tcp    规划/TCP坐标系
```

`base_link` 没有实体几何，`b0` 是机器人底座；`gripper_base` 固定安装在 `l6` 上，不包含夹爪开合；`grasp_tcp` 是无 visual/collision 的工具坐标系。`grasp_tcp.STL` 为空占位文件，因此不在仓库中，URDF 也不引用它。

## 构建和预览

```bash
source /opt/ros/humble/setup.bash
cd <仓库路径>/ROS2/Humble
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select cr7as_grasp
source install/setup.bash
ros2 launch cr7as_grasp display.launch.py
```

## Gazebo Classic 控制

```bash
ros2 launch cr7as_grasp gazebo_control.launch.py
ros2 control list_controllers -c /controller_manager
```

预期 `joint_state_broadcaster` 和 `arm_controller` 为 `active`。轨迹测试示例：

```bash
ros2 topic pub --once /arm_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory \
  "{joint_names: ['j1','j2','j3','j4','j5','j6'], points: [{positions: [0.2, -0.3, 0.4, 0.0, 0.2, 0.0], time_from_start: {sec: 4, nanosec: 0}}]}"
```

## 限制

- 末端是固定工具，不是可开合二指夹爪；
- `effort`、`velocity`、阻尼、摩擦、质量和惯量是当前仿真值或近似值，不能直接作为实机参数；
- visual 与 collision 复用详细 STL，碰撞规划前应制作简化网格；
- 本包使用 Gazebo Classic，不适用于 Gazebo Sim / Ignition 的插件体系。
