import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_path = get_package_share_directory('four_wheel_robot_description')
    slam_params = os.path.join(pkg_path, 'config', 'slam_toolbox.yaml')
    rviz_config = os.path.join(pkg_path, 'config', 'slam.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock',
    )

    # Include robot + Gazebo launch
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, 'launch', 'gazebo.launch.py')
        ),
    )

    # SLAM Toolbox — online async mode
    slam_toolbox = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[slam_params, {'use_sim_time': use_sim_time}],
        output='screen',
    )

    # RViz for SLAM visualization
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        use_sim_time_arg,
        gazebo_launch,
        slam_toolbox,
        rviz,
    ])
