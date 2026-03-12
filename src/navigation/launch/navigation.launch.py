"""
Autonomous Navigation Launch File
==================================
Launches the full Navigation2 stack:
  1. Gazebo simulation with the four-wheel robot
  2. Nav2 bringup (AMCL + map_server + planners + controller + behaviors)
  3. cmd_vel relay to diff_drive_controller
  4. RViz2 configured for navigation visualization

Prerequisites:
  - A saved map from slam_package (map.yaml + map.pgm)

Usage:
  ros2 launch navigation navigation.launch.py \
      map:=/path/to/your/map.yaml

  # In RViz:
  # 1. Use "2D Pose Estimate" to set the robot's initial position
  # 2. Use "Nav2 Goal" to send a navigation goal
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    nav_pkg = get_package_share_directory('navigation')
    robot_pkg = get_package_share_directory('four_wheel_robot_description')

    loc_pkg = get_package_share_directory('localization')

    nav2_params = os.path.join(nav_pkg, 'config', 'nav2_params.yaml')
    rviz_config = os.path.join(nav_pkg, 'config', 'navigation.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_file = LaunchConfiguration('map')

    # ── Launch Arguments ──────────────────────────────────
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation clock',
    )

    map_arg = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(loc_pkg, 'maps', 'map.yaml'),
        description='Path to map YAML file',
    )

    # ── Gazebo + Robot + Controllers ──────────────────────
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_pkg, 'launch', 'gazebo.launch.py')
        ),
    )

    # ── Nav2 Bringup ──────────────────────────────────────
    # Launches: map_server, AMCL, planner_server, controller_server,
    #           behavior_server, bt_navigator, lifecycle_manager
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

    # ── cmd_vel relay ─────────────────────────────────────
    # Nav2 outputs on /cmd_vel (Twist).
    # diff_drive_controller expects /diff_drive_controller/cmd_vel_unstamped.
    # This relay bridges the two topics.
    cmd_vel_relay = Node(
        package='topic_tools',
        executable='relay',
        name='cmd_vel_relay',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['/cmd_vel', '/diff_drive_controller/cmd_vel_unstamped'],
        output='screen',
    )

    # ── RViz2 ─────────────────────────────────────────────
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        use_sim_time_arg,
        map_arg,
        gazebo_launch,
        nav2_launch,
        cmd_vel_relay,
        rviz_node,
    ])
