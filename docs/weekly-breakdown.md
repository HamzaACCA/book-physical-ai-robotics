---
sidebar_position: 6
---

# Weekly Breakdown

## Weeks 1-2: Introduction to Physical AI

**Theme**: From Digital AI to Embodied Intelligence

### Learning Objectives
- Understand Physical AI principles and embodied intelligence
- Transition from AI models confined to digital environments to robots operating in physical space
- Overview of humanoid robotics landscape
- Introduction to sensor systems

### Topics Covered
- 🤖 **Foundations of Physical AI**: What makes AI "physical"?
- 🌍 **Embodied Intelligence**: Robots that understand physical laws
- 📡 **Sensor Systems**:
  - LiDAR (Light Detection and Ranging)
  - Cameras (RGB, Depth, Stereo)
  - IMUs (Inertial Measurement Units)
  - Force/Torque Sensors

### Hands-On Activities
- Explore sensor data from different modalities
- Compare digital AI (ChatGPT) vs. embodied AI (robot navigation)
- Review humanoid robot demonstrations (Boston Dynamics, Unitree, Tesla Bot)

---

## Weeks 3-5: ROS 2 Fundamentals

**Theme**: The Robotic Nervous System

### Learning Objectives
- Master ROS 2 architecture and core concepts
- Build ROS 2 packages with Python
- Understand communication patterns (topics, services, actions)
- Configure robot launch files

### Week 3: ROS 2 Architecture
- Nodes, topics, and publishers/subscribers
- Message types and custom messages
- Setting up a ROS 2 workspace

### Week 4: Services and Actions
- Request-response patterns with services
- Long-running tasks with actions
- Action feedback and cancellation

### Week 5: Building Packages
- Python package structure with `rclpy`
- Launch files for multi-node systems
- Parameter management and configuration

### Hands-On Projects
- **Project 1**: Build a sensor-to-actuator pipeline
- **Project 2**: Create a teleoperation system (keyboard → robot movement)
- **Project 3**: Implement a simple state machine with ROS 2 actions

---

## Weeks 6-7: Robot Simulation with Gazebo

**Theme**: The Digital Twin

### Learning Objectives
- Set up Gazebo simulation environment
- Define robots using URDF and SDF formats
- Simulate physics (gravity, collisions, friction)
- Add sensors to simulated robots
- Introduction to Unity for high-fidelity visualization

### Week 6: Gazebo Basics
- Installing and configuring Gazebo
- Loading URDF models
- World files and environment design
- Physics engine configuration

### Week 7: Advanced Simulation
- Sensor plugins (LiDAR, cameras, IMU)
- Contact sensors and force feedback
- Integrating Gazebo with ROS 2
- Unity integration for rendering

### Hands-On Projects
- **Project 1**: Load a humanoid URDF and make it stand
- **Project 2**: Add a depth camera and visualize point clouds
- **Project 3**: Create a cluttered environment for navigation testing

---

## Weeks 8-10: NVIDIA Isaac Platform

**Theme**: The AI-Robot Brain

### Learning Objectives
- Work with NVIDIA Isaac SDK and Isaac Sim
- Implement AI-powered perception and manipulation
- Use reinforcement learning for robot control
- Master sim-to-real transfer techniques

### Week 8: Isaac Sim Setup
- NVIDIA Omniverse installation
- Isaac Sim environment and robot loading
- Photorealistic rendering and synthetic data generation

### Week 9: Isaac ROS Perception
- VSLAM (Visual SLAM) pipeline
- Object detection with DeepStream
- Hardware acceleration on Jetson

### Week 10: Navigation and Manipulation
- Nav2 integration for path planning
- Grasping with humanoid hands
- Reinforcement learning for locomotion

### Hands-On Projects
- **Project 1**: Set up Isaac Sim with a humanoid robot
- **Project 2**: Build a VSLAM map of a simulated environment
- **Project 3**: Implement object detection and tracking
- **Project 4**: Train a walking controller with RL

---

## Weeks 11-12: Humanoid Robot Development

**Theme**: Bipedal Intelligence

### Learning Objectives
- Understand humanoid robot kinematics and dynamics
- Implement bipedal locomotion and balance control
- Master manipulation and grasping with humanoid hands
- Design natural human-robot interactions

### Week 11: Bipedal Locomotion
- Kinematics: Forward and inverse kinematics
- Dynamics: Zero-Moment Point (ZMP) and balance
- Gait patterns (walking, running, turning)
- Fall detection and recovery

### Week 12: Manipulation and Interaction
- Humanoid hand control (position, force, impedance)
- Grasping strategies (power grip, precision grip)
- Human-robot interaction design (proxemics, gestures)
- Safety considerations

### Hands-On Projects
- **Project 1**: Implement a walking controller for a simulated humanoid
- **Project 2**: Program a humanoid hand to grasp various objects
- **Project 3**: Design a human-robot handshake interaction

---

## Week 13: Conversational Robotics

**Theme**: Voice-Language-Action

### Learning Objectives
- Integrate GPT models for conversational AI in robots
- Implement speech recognition and natural language understanding
- Build multi-modal interaction systems (speech, gesture, vision)
- Complete the capstone project

### Topics Covered
- **Speech Recognition**: OpenAI Whisper integration
- **LLM Planning**: Translating natural language to robot actions
- **Multi-Modal Fusion**: Combining speech, vision, and gesture
- **System Integration**: End-to-end autonomous pipeline

### Capstone Project Presentations
Students present their **Autonomous Humanoid** projects:
- Voice command → LLM planning → Navigation → Object detection → Manipulation

### Evaluation Criteria
- ✅ Successful voice command recognition
- ✅ Correct action plan generation
- ✅ Obstacle-free navigation
- ✅ Accurate object identification
- ✅ Successful object manipulation
- ✅ Robustness to variations

---

## Weekly Time Commitment

| Activity | Hours/Week |
|----------|------------|
| Lectures | 3-4 hours |
| Hands-On Labs | 4-6 hours |
| Project Work | 5-8 hours |
| Reading/Research | 2-3 hours |
| **Total** | **14-21 hours** |

:::tip
This is an intensive capstone course. Budget 15-20 hours per week for optimal learning.
:::
