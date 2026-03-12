"""
SLAM Mapping Launch File
========================
Launches the full SLAM pipeline:
  1. Gazebo simulation with the four-wheel robot
  2. slam_toolbox in online async mapping mode
  3. RViz2 configured for map visualization

Usage:
  ros2 launch slam_package slam.launch.py

  # Drive the robot to build the map:
  ros2 run teleop_twist_keyboard teleop_twist_keyboard \
      --ros-args -r /cmd_vel:=/diff_drive_controller/cmd_vel_unstamped

  # Save the map when done:
  ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/slam_package/maps/my_map
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    slam_pkg = get_package_share_directory('slam_package')
    robot_pkg = get_package_share_directory('four_wheel_robot_description')

    slam_params = os.path.join(slam_pkg, 'config', 'slam.yaml')
    rviz_config = os.path.join(slam_pkg, 'config', 'slam.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time')

    # ── Launch arguments ──────────────────────────────────
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation clock',
    )

    # ── Gazebo + Robot + Controllers ──────────────────────
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(robot_pkg, 'launch', 'gazebo.launch.py')
        ),
    )

    # ── slam_toolbox — Online Async SLAM ──────────────────
    # Subscribes to /scan and TF (odom → base_footprint)
    # Publishes /map, /map_metadata, and TF (map → odom)
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[slam_params, {'use_sim_time': use_sim_time}],
        output='screen',
    )

    # ── RViz2 — Map Visualization ─────────────────────────
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
        gazebo_launch,
        slam_toolbox_node,
        rviz_node,
    ])
