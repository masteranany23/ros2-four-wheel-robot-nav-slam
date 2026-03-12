"""
AMCL Localization Launch File
=============================
Launches the full localization pipeline:
  1. Gazebo simulation with the four-wheel robot
  2. Map server (loads a pre-built map)
  3. AMCL particle filter for pose estimation
  4. Lifecycle manager to activate localization nodes
  5. RViz2 configured for localization visualization

Prerequisites:
  - A saved map from slam_package (map.yaml + map.pgm)

Usage:
  ros2 launch localization localization.launch.py \
      map:=/path/to/your/map.yaml

  # In RViz, use "2D Pose Estimate" tool to set the initial pose,
  # then drive the robot to verify localization:
  ros2 run teleop_twist_keyboard teleop_twist_keyboard \
      --ros-args -r /cmd_vel:=/diff_drive_controller/cmd_vel_unstamped
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    loc_pkg = get_package_share_directory('localization')
    robot_pkg = get_package_share_directory('four_wheel_robot_description')

    amcl_params = os.path.join(loc_pkg, 'config', 'amcl.yaml')
    rviz_config = os.path.join(loc_pkg, 'config', 'localization.rviz')

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
        description='Path to map YAML (from slam_toolbox map_saver)',
    )

    # ── Gazebo + Robot + Controllers ──────────────────────
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_pkg, 'launch', 'gazebo.launch.py')
        ),
    )

    # ── Map Server ────────────────────────────────────────
    # Loads the pre-built occupancy grid map and publishes on /map
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        parameters=[
            amcl_params,
            {
                'use_sim_time': use_sim_time,
                'yaml_filename': map_file,
            },
        ],
        output='screen',
    )

    # ── AMCL — Adaptive Monte Carlo Localization ──────────
    # Subscribes to /scan, /map, TF (odom → base_footprint)
    # Publishes /amcl_pose and TF (map → odom)
    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        parameters=[amcl_params, {'use_sim_time': use_sim_time}],
        output='screen',
    )

    # ── Lifecycle Manager ─────────────────────────────────
    # AMCL and map_server are lifecycle nodes; this manager
    # transitions them through configure → activate automatically
    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'autostart': True},
            {'node_names': ['map_server', 'amcl']},
        ],
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
        map_server_node,
        amcl_node,
        lifecycle_manager_node,
        rviz_node,
    ])
