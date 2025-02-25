#!/usr/bin/env python3
#最小構成でlimeをgazeboに出す
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import ThisLaunchFileDir
from launch.substitutions import Command
from launch.substitutions import FindExecutable
from launch.conditions import IfCondition
from launch.conditions import UnlessCondition

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    ld = LaunchDescription()

    #limeの初期pose
    pose = {'x': LaunchConfiguration('x_pose', default='-2.00'),
            'y': LaunchConfiguration('y_pose', default='-0.50'),
            'z': LaunchConfiguration('z_pose', default='0.01'),}
            #'R': LaunchConfiguration('roll', default='0.00'),
            #'P': LaunchConfiguration('pitch', default='0.00'),
            #'Y': LaunchConfiguration('yaw', default='0.00')}

    world = LaunchConfiguration( #設置ワールド
        'world',
        default=PathJoinSubstitution(
            [
                FindPackageShare('turtlebot3_lime_bringup'),
                'worlds',
                'turtlebot3_world.model'
            ]
        )
    )
    use_sim = LaunchConfiguration('use_sim', default='true') #simulationモードにする

    urdf_file = Command( #gazebo->urdf？
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [
                    FindPackageShare('turtlebot3_lime_description'),
                    'urdf',
                    'turtlebot3_lime.urdf.xacro'
                ]
            ),
            ' ',
            'use_sim:=',
            use_sim,
            ' ',
        ]
    )

    controller_manager_config = PathJoinSubstitution(
        [
            FindPackageShare('turtlebot3_lime_bringup'),
            'config',
            'hardware_controller_manager.yaml',
        ]
    )

    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            {'robot_description': urdf_file},
            controller_manager_config
        ],
        remappings=[
            ('~/cmd_vel_unstamped', 'cmd_vel'),
            ('~/odom', 'odom')
        ],
        output="both",
        condition=UnlessCondition(use_sim))

    robot_state_pub_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': urdf_file, 'use_sim_time': use_sim}],
        output='screen'
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    gazebo = IncludeLaunchDescription( #gazeboの起動
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare('gazebo_ros'),
                        'launch',
                        'gazebo.launch.py'
                    ]
                )
            ]
        ),
        launch_arguments={
            'world': world
        }.items(),
    )

    spawn_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'turtlebot3_lime_system',
            '-x', pose['x'], '-y', pose['y'], '-z', pose['z'],
            #'-R', pose['R'], '-P', pose['P'], '-Y', pose['Y'],
            ],
        output='screen',
    )

    ld.add_action(control_node)
    ld.add_action(robot_state_pub_node)
    ld.add_action(joint_state_broadcaster_spawner)
    ld.add_action(gazebo)
    ld.add_action(spawn_node)

    return ld
