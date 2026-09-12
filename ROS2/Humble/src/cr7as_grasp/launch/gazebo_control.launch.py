import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():

    # 获取本功能包和 gazebo_ros 的安装目录
    package_share = get_package_share_directory('cr7as_grasp')
    gazebo_share = get_package_share_directory('gazebo_ros')

    # 让 Gazebo Classic 可以解析：
    # package://cr7as_grasp/meshes/xxx.STL
    share_directory = os.path.dirname(package_share)
    old_model_path = os.environ.get('GAZEBO_MODEL_PATH', '')

    model_path = share_directory
    if old_model_path:
        model_path += os.pathsep + old_model_path

    set_gazebo_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH',
        value=model_path
    )

    # URDF 与控制器 YAML 的实际路径
    urdf_path = os.path.join(
        package_share,
        'urdf',
        'cr7as_grasp_gazebo.urdf'
    )

    controller_yaml = os.path.join(
        package_share,
        'config',
        'gazebo_controllers.yaml'
    )

    # 读取 URDF 文本
    with open(urdf_path, 'r') as urdf_file:
        robot_description = urdf_file.read()

    # 普通 URDF 不是 xacro，不能自动解析 $(find ...)
    # 因此在 launch 内替换成真实的绝对路径。
    robot_description = robot_description.replace(
        '$(find cr7as_grasp)/config/gazebo_controllers.yaml',
        controller_yaml,
    )

    # 启动 Gazebo Classic
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                gazebo_share,
                'launch',
                'gazebo.launch.py'
            )
        )
    )

    # 将 robot_description 参数发布给 robot_state_publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description,
                'use_sim_time': True,
            }
        ],
    )

    # 从 robot_description 话题中读取 URDF，并生成 Gazebo 实体
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'cr7as_grasp',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.10',
        ],
    )

    # 启动关节状态发布控制器
    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=[
            'joint_state_broadcaster',
            '-c', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
    )

    # 启动六轴机械臂轨迹控制器
    arm_controller = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=[
            'arm_controller',
            '-c', '/controller_manager',
            '--controller-manager-timeout', '60',
        ],
    )

    # 机器人成功生成后，再启动控制器。
    # 这样比 launch 一开始就固定计时更稳妥。
    start_controllers_after_spawn = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_robot,
            on_exit=[
                TimerAction(
                    period=3.0,
                    actions=[joint_state_broadcaster],
                ),
                TimerAction(
                    period=5.0,
                    actions=[arm_controller],
                ),
            ],
        )
    )

    return LaunchDescription([
        set_gazebo_model_path,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        start_controllers_after_spawn,
    ])
