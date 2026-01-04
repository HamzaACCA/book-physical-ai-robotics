---
sidebar_position: 2
---

# Quarter Overview

The future of AI extends beyond digital spaces into the physical world. This capstone quarter introduces **Physical AI**—AI systems that function in reality and comprehend physical laws.

Students learn to design, simulate, and deploy humanoid robots capable of natural human interactions using:

- **ROS 2** (Robot Operating System 2)
- **Gazebo** (Physics Simulation)
- **Unity** (High-Fidelity Rendering)
- **NVIDIA Isaac** (AI-Powered Robotics Platform)

## The Journey

This course takes you from understanding robotic middleware to deploying AI-powered humanoid robots:

```mermaid
graph LR
    A[Digital AI] --> B[Physical AI Principles]
    B --> C[ROS 2 Control]
    C --> D[Physics Simulation]
    D --> E[NVIDIA Isaac]
    E --> F[Voice-Language-Action]
    F --> G[Autonomous Humanoid]
```

## Capstone Project: The Autonomous Humanoid

Your final project will demonstrate the complete Physical AI pipeline:

1. **Voice Input**: Receive a natural language command (e.g., "Clean the room")
2. **Cognitive Planning**: Use an LLM to break down the command into ROS 2 actions
3. **Path Planning**: Navigate obstacles using Nav2
4. **Object Detection**: Identify targets using computer vision
5. **Manipulation**: Pick up and interact with objects
6. **Execution**: Complete the task autonomously in simulation

All of this runs in a **simulated environment** first, with optional deployment to real hardware.
