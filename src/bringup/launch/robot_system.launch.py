"""
Master Robot System Launch File
================================
Launches the COMPLETE robot system with selectable mode:

  Mode 1 — SLAM (default):
    Gazebo + Robot + Controllers + slam_toolbox + RViz
    Use this to explore and build a map.

  Mode 2 — NAV (navigation with pre-built map):
    Gazebo + Robot + Controllers + AMCL + Nav2 stack + cmd_vel relay + RViz
    Use this for autonomous navigation with a saved map.

Usage:
  # SLAM mode (explore and build a map):
  ros2 launch bringup robot_system.launch.py mode:=slam

  # Navigation mode (autonomous navigation with saved map):
  ros2 launch bringup robot_system.launch.py mode:=nav map:=/path/to/map.yaml

  # Drive the robot (SLAM mode):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard \\
      --ros-args -r /cmd_vel:=/diff_drive_controller/cmd_vel_unstamped

  # Save map after SLAM:
  ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/maps/my_map
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context):
    """Resolve the mode argument and return the appropriate nodes."""

    mode = LaunchConfiguration('mode').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time')

    robot_pkg = get_package_share_directory('four_wheel_robot_description')
    slam_pkg = get_package_share_directory('slam_package')
    loc_pkg = get_package_share_directory('localization')
    nav_pkg = get_package_share_directory('navigation')

    nodes = []

    # ── 1. Gazebo Simulation + Robot Spawn + Controllers ──
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_pkg, 'launch', 'gazebo.launch.py')
        ),
    )
    nodes.append(gazebo_launch)

    if mode == 'slam':
        # ── 2a. SLAM Mode ────────────────────────────────
        # slam_toolbox for mapping, no AMCL or Nav2 needed
        slam_params = os.path.join(slam_pkg, 'config', 'slam.yaml')
        rviz_config = os.path.join(slam_pkg, 'config', 'slam.rviz')

        slam_node = Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            parameters=[slam_params, {'use_sim_time': use_sim_time}],
            output='screen',
        )
        nodes.append(slam_node)

        rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        )
        nodes.append(rviz_node)

    elif mode == 'nav':
        # ── 2b. Navigation Mode ──────────────────────────
        # AMCL + Nav2 stack + cmd_vel relay
        map_file = LaunchConfiguration('map')
        nav2_params = os.path.join(nav_pkg, 'config', 'nav2_params.yaml')
        rviz_config = os.path.join(nav_pkg, 'config', 'navigation.rviz')

        nav2_bringup_path = get_package_share_directory('nav2_bringup')
        nav2_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_path, 'launch', 'bringup_launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'params_file': nav2_params,
                'map': map_file,
            }.items(),
        )
        nodes.append(nav2_launch)

        # Relay /cmd_vel → /diff_drive_controller/cmd_vel_unstamped
        cmd_vel_relay = Node(
            package='topic_tools',
            executable='relay',
            name='cmd_vel_relay',
            parameters=[{'use_sim_time': use_sim_time}],
            arguments=['/cmd_vel', '/diff_drive_controller/cmd_vel_unstamped'],
            output='screen',
        )
        nodes.append(cmd_vel_relay)

        rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        )
        nodes.append(rviz_node)

    else:
        raise ValueError(f"Unknown mode '{mode}'. Use 'slam' or 'nav'.")

    return nodes


def generate_launch_description():

    loc_pkg = get_package_share_directory('localization')

    return LaunchDescription([
        # ── Arguments ─────────────────────────────────────
        DeclareLaunchArgument(
            'mode',
            default_value='slam',
            description="System mode: 'slam' (build map) or 'nav' (navigate with map)",
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use Gazebo simulation clock',
        ),
        DeclareLaunchArgument(
            'map',
            default_value=os.path.join(loc_pkg, 'maps', 'map.yaml'),
            description='Path to map YAML file (nav mode only)',
        ),

        # ── Conditional launch based on mode ──────────────
        OpaqueFunction(function=launch_setup),
    ])
