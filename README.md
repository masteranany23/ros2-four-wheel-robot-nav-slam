# ros2-four-wheel-robot-nav

A ROS 2 four-wheel differential drive robot with SLAM, localization, and autonomous navigation in Gazebo simulation.

![ROS 2](https://img.shields.io/badge/ROS%202-Humble-blue)
![Gazebo](https://img.shields.io/badge/Gazebo-Classic-orange)

## Overview

This project simulates a 4-wheel robot equipped with a 2D LiDAR and IMU, capable of:

- **Mapping** an environment using SLAM Toolbox
- **Localizing** on a saved map using AMCL
- **Navigating autonomously** using Nav2

## Packages

| Package | Description |
|---------|-------------|
| `four_wheel_robot_description` | Robot URDF, Gazebo world, sensor configs, RViz configs |
| `bringup` | Top-level launch (SLAM / NAV mode) |
| `slam_package` | SLAM Toolbox integration for map building |
| `localization` | AMCL particle filter for pose estimation |
| `navigation` | Nav2 stack with NavFn + DWB planners |

## Robot Specs

- **Chassis:** 0.6 × 0.4 × 0.15 m, ~12.5 kg
- **Drive:** Differential drive, 4 wheels (0.1 m radius)
- **LiDAR:** 360°, 12 m range, 10 Hz
- **IMU:** 100 Hz, angular velocity + linear acceleration
- **World:** 10 × 10 m arena with obstacle boxes

## Usage

### Build

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### 1. SLAM (Build a Map)

```bash
ros2 launch bringup robot_system.launch.py mode:=slam
```

Drive the robot with teleop:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_drive_controller/cmd_vel_unstamped
```

Save the map:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/maps/my_map
```

### 2. Localization

```bash
ros2 launch localization localization.launch.py map:=/path/to/map.yaml
```

Set initial pose using the **2D Pose Estimate** tool in RViz.

### 3. Autonomous Navigation

```bash
ros2 launch bringup robot_system.launch.py mode:=nav map:=/path/to/map.yaml
```

Set the robot's pose, then send goals using **Nav2 Goal** in RViz.

## Dependencies

- ROS 2 (Humble)
- Gazebo Classic
- `ros2_control`, `gazebo_ros2_control`
- `slam_toolbox`
- `nav2_bringup`, `nav2_map_server`, `nav2_amcl`
- `teleop_twist_keyboard`
