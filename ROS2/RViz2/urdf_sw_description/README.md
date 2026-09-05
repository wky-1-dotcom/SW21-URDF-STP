# urdf_sw_description

本包由 SolidWorks SW2URDF 导出的 ROS 1 包 `URDF-SW` 转换而来，用于
ROS 2 Foxy 中的 robot_state_publisher、Joint State Publisher GUI 和 RViz2 显示。
原始 F 盘目录没有修改。

## 放入工作空间

将整个 `urdf_sw_description` 目录复制到：

```text
~/Desktop/dev_ws/src/urdf_sw_description
```

不能只复制 URDF，因为模型还依赖 `meshes`、`launch`、`rviz`、
`package.xml` 和 `CMakeLists.txt`。

## 构建和启动（ROS 2 Foxy）

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/dev_ws
colcon build --symlink-install --packages-select urdf_sw_description
source install/setup.bash
ros2 launch urdf_sw_description display.launch.py
```

## 转换说明

- 增加了固定根坐标系 `base_link`；
- 包名、机器人名、URDF 文件名和所有 mesh URI 已改为 ROS 2 友好格式；
- `link` 和 `jlink` 分别改名为 `gripper_link` 和 `gripper_slider_joint`；
- 原导出文件错误地让直线滑块 mimic 腕关节 `j6`，该关系已删除；
- 机械臂 `j1` 到 `j6` 保留导出的 `-1.57` 到 `1.57 rad` 显示范围；
- 滑块使用临时 `-0.02` 到 `0.02 m` 显示范围。

这些限位、effort 和 velocity 不是厂家或实机安全参数。用于 Gazebo、MoveIt 2、
ros2_control 或真实机械臂前，必须根据厂家数据、丝杠导程和实际机械行程重新确认。
