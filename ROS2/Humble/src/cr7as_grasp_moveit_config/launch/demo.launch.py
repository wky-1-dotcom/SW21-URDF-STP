from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config_share = get_package_share_directory("cr7as_grasp_moveit_config")
    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(config_share, "launch", "move_group.launch.py"))
    )
    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(config_share, "launch", "moveit_rviz.launch.py"))
    )
    return LaunchDescription([move_group, rviz])
