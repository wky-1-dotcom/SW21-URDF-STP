# DOBOT CR7 gripper v6 description

This ROS 2 package was converted from the SolidWorks export in
`机械臂+末端执行器-6`.

## Build and display

```bash
source /opt/ros/foxy/setup.bash
cd ~/Desktop/dev_ws
colcon build --symlink-install --packages-select dobot_cr7_gripper_v6_description
source install/setup.bash
ros2 launch dobot_cr7_gripper_v6_description display.launch.py
```

Copy this complete directory into `~/Desktop/dev_ws/src`; do not copy only
the URDF because it references the files in `meshes`.

## Limits and gripper linkage

The SolidWorks export supplied arm limits of -1.57 to 1.57 radians. Nonzero
effort and velocity values were added so ROS tools can use those joints. The
gripper limits are temporary visualization ranges.

The five exported mimic joints still use `j7` with a multiplier of `1`.
Validate the pin alignment throughout the motion range. A closed-loop gripper
may require corrected multipliers, a custom joint-state calculation node, or a
simplified tree model.

These values are not approved for MoveIt 2, Gazebo, ros2_control, or real
hardware. Replace them with verified manufacturer and mechanism data first.
