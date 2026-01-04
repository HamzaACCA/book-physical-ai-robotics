---
sidebar_position: 2
---

# Module 2: The Digital Twin (Gazebo & Unity)

**Focus**: Physics simulation and environment building

## Why Simulation?

Before deploying AI to expensive hardware, we test in **digital twins**—virtual replicas of robots and environments that obey real-world physics.

## Gazebo: Physics Simulation

**Gazebo** is the industry-standard physics simulator for robotics. It simulates:

- ⚙️ **Gravity and Rigid Body Dynamics**
- 🔨 **Collisions and Friction**
- 📡 **Sensor Data** (LiDAR, cameras, IMUs)

### Simulating Physics

```xml
<world name="default">
  <physics type="ode">
    <gravity>0 0 -9.81</gravity>
    <max_step_size>0.001</max_step_size>
    <real_time_factor>1.0</real_time_factor>
  </physics>
</world>
```

### Example: Humanoid in Gazebo

Your humanoid robot will be loaded from a URDF file into Gazebo, where it can:
- Walk on uneven terrain
- Respond to external forces (pushes, wind)
- Interact with objects (pick up, throw)

## Unity: High-Fidelity Rendering

While Gazebo handles physics, **Unity** provides:

- 🎨 **Photorealistic Graphics** for human-robot interaction studies
- 🧑‍🤝‍🧑 **Human Models** for social robotics scenarios
- 🌍 **Complex Environments** (homes, offices, factories)

### Unity ML-Agents Integration

Unity can be integrated with ROS 2 to train robots in visually rich environments:

```csharp
public class HumanoidAgent : Agent
{
    public override void OnActionReceived(ActionBuffers actions)
    {
        // Apply actions from ROS 2 or ML model
        float torque = actions.ContinuousActions[0];
        rb.AddTorque(Vector3.forward * torque);
    }
}
```

## Simulating Sensors

### LiDAR (Light Detection and Ranging)

Measures distance by emitting laser pulses:

```xml
<sensor name="lidar" type="ray">
  <ray>
    <scan>
      <horizontal>
        <samples>360</samples>
        <min_angle>-3.14</min_angle>
        <max_angle>3.14</max_angle>
      </horizontal>
    </scan>
    <range>
      <min>0.1</min>
      <max>30.0</max>
    </range>
  </ray>
</sensor>
```

### Depth Cameras

Provide RGB (color) + Depth (distance) information:
- Used for 3D object detection
- Essential for manipulation tasks
- Feeds data to computer vision models

### IMUs (Inertial Measurement Units)

Measure orientation and acceleration:
- Critical for balance control in bipedal robots
- Detects falls and instability
- Fuses with vision for robust localization

## Learning Objectives

### Week 6-7 Coverage

1. **Gazebo Environment Setup**: Install and configure simulation
2. **URDF and SDF Robot Descriptions**: Define robot geometry and physics
3. **Physics Simulation**: Configure gravity, collisions, and friction
4. **Sensor Simulation**: Add LiDAR, cameras, and IMUs to your robot
5. **Unity for Visualization**: Create high-fidelity environments

## Hands-On Projects

1. **Gazebo Simulation**: Load a humanoid URDF and make it stand
2. **Sensor Integration**: Add a depth camera and visualize point clouds
3. **Unity Environment**: Build a room with furniture for the robot to navigate
