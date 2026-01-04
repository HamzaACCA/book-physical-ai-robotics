---
sidebar_position: 1
---

# Module 1: The Robotic Nervous System (ROS 2)

**Focus**: Middleware for robot control

## What is ROS 2?

ROS 2 (Robot Operating System 2) is the nervous system of modern robots. It's a middleware framework that allows different parts of a robot to communicate seamlessly.

## Key Concepts

### Nodes, Topics, and Services

- **Nodes**: Independent programs that perform specific tasks (e.g., motor controller, sensor reader, path planner)
- **Topics**: Communication channels where nodes publish and subscribe to data
- **Services**: Request-response communication between nodes

### Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Sensor     │      │   Brain     │      │  Actuator   │
│  Node       │─────▶│   Node      │─────▶│  Node       │
│ (Publisher) │      │(Subscriber) │      │(Subscriber) │
└─────────────┘      └─────────────┘      └─────────────┘
      │                    │                     │
      └────────────────────┴─────────────────────┘
                 ROS 2 Middleware
```

## Learning Objectives

### Week 3-5 Coverage

1. **ROS 2 Architecture**: Understand the core concepts and design philosophy
2. **Nodes, Topics, Services, and Actions**: Build communication systems
3. **Building ROS 2 Packages with Python**: Use `rclpy` to create Python-based nodes
4. **Launch Files and Parameter Management**: Automate robot startup and configuration

## Bridging Python Agents to ROS

One of the most powerful aspects of ROS 2 is integrating AI agents (trained in Python) with robotic hardware:

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class HumanoidController(Node):
    def __init__(self):
        super().__init__('humanoid_controller')
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        
    def move_forward(self, speed):
        msg = Twist()
        msg.linear.x = speed
        self.publisher.publish(msg)
```

## Understanding URDF for Humanoids

**URDF (Unified Robot Description Format)** is an XML format for describing robot geometry, kinematics, and dynamics.

### Example: Humanoid Arm Link

```xml
<link name="upper_arm">
  <visual>
    <geometry>
      <cylinder length="0.3" radius="0.05"/>
    </geometry>
  </visual>
  <collision>
    <geometry>
      <cylinder length="0.3" radius="0.05"/>
    </geometry>
  </collision>
  <inertial>
    <mass value="1.0"/>
    <inertia ixx="0.01" ixy="0.0" ixz="0.0" 
             iyy="0.01" iyz="0.0" izz="0.001"/>
  </inertial>
</link>
```

## Hands-On Projects

1. **ROS 2 Package Development**: Create a sensor-to-actuator pipeline
2. **URDF Modeling**: Design a simple humanoid arm
3. **Integration Test**: Connect a Python AI agent to ROS 2 control nodes
