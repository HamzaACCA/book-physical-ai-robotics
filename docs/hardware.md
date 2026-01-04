---
sidebar_position: 5
---

# Hardware Requirements

This course is technically demanding. It sits at the intersection of three heavy computational loads:

- ⚙️ **Physics Simulation** (Isaac Sim/Gazebo)
- 👁️ **Visual Perception** (SLAM/Computer Vision)
- 🧠 **Generative AI** (LLMs/VLA)

## Two Implementation Options

### Option 1: High CapEx - On-Premise Lab
Build a physical lab at home with powerful workstations and robot hardware.

### Option 2: High OpEx - Cloud-Native Lab
Rent cloud instances for simulation and use edge devices for physical deployment.

---

## 1. The "Digital Twin" Workstation (Required)

This is the **most critical component**. NVIDIA Isaac Sim requires RTX (Ray Tracing) capabilities.

### Minimum Specifications

| Component | Requirement | Why |
|-----------|-------------|-----|
| **GPU** | NVIDIA RTX 4070 Ti (12GB VRAM) or higher | Isaac Sim needs high VRAM for USD assets + VLA models |
| **Ideal GPU** | RTX 3090 or 4090 (24GB VRAM) | Smoother sim-to-real training |
| **CPU** | Intel Core i7 (13th Gen+) or AMD Ryzen 9 | Physics calculations are CPU-intensive |
| **RAM** | 64 GB DDR5 (32 GB minimum) | Complex scene rendering |
| **OS** | Ubuntu 22.04 LTS | ROS 2 (Humble/Iron) is native to Linux |

:::warning
Standard laptops (MacBooks or non-RTX Windows machines) **will not work** for Isaac Sim.
:::

### Why These Specs?

- **High VRAM**: Load robot and environment assets simultaneously
- **RTX GPU**: Ray tracing for photorealistic rendering
- **Linux**: ROS 2 is native to Ubuntu; Windows requires WSL2 (adds friction)

---

## 2. The "Physical AI" Edge Kit

Students learn Physical AI by setting up the nervous system before deploying to a robot.

### The Economy Jetson Student Kit (~$700)

| Component | Model | Price | Notes |
|-----------|-------|-------|-------|
| **Brain** | NVIDIA Jetson Orin Nano Super (8GB) | $249 | 40 TOPS, price dropped from $499 |
| **Eyes** | Intel RealSense D435i | $349 | Includes IMU for SLAM |
| **Ears** | ReSpeaker USB Mic Array v2.0 | $69 | Far-field microphone for voice |
| **Storage** | 128GB microSD (high-endurance) | $30 | OS and models |
| **Total** | | **~$700** | Per student kit |

### What This Kit Enables

- ✅ Deploy ROS 2 nodes on edge hardware
- ✅ Run VSLAM (Visual SLAM) in real-time
- ✅ Understand resource constraints vs. workstations
- ✅ Test voice-to-action pipelines
- ✅ Prepare for robot deployment

---

## 3. The Robot Lab (Optional but Recommended)

### Option A: The "Proxy" Approach (Budget-Friendly)

Use a **quadruped** or **robotic arm** as a proxy. Software principles transfer 90% to humanoids.

**Recommended Robot**: Unitree Go2 Edu (~$1,800 - $3,000)

**Pros**:
- ✅ Highly durable
- ✅ Excellent ROS 2 support
- ✅ Affordable for multiple units

**Cons**:
- ❌ Not a biped (humanoid)

### Option B: The "Miniature Humanoid" Approach

Small, table-top humanoids.

| Robot | Price | Notes |
|-------|-------|-------|
| Unitree G1 | ~$16,000 | Commercially available, dynamic walking |
| Robotis OP3 | ~$12,000 | Older but stable |
| Hiwonder TonyPi Pro | ~$600 | Budget option (Raspberry Pi, limited AI) |

:::caution
Cheap kits (Hiwonder) run on Raspberry Pi and **cannot run NVIDIA Isaac ROS efficiently**. Use Jetson kits for AI.
:::

### Option C: The "Premium" Lab (Sim-to-Real)

For actual deployment to a real humanoid:

**Robot**: Unitree G1 Humanoid (~$16,000)

**Why**: One of the few commercially available humanoids with:
- Dynamic walking capability
- Open SDK for custom ROS 2 controllers
- Research community support

---

## 4. Cloud-Native Alternative (High OpEx)

If you lack RTX-enabled workstations, use **cloud instances**.

### AWS Setup

**Instance Type**: AWS `g5.2xlarge` (A10G GPU, 24GB VRAM)

**Software**: NVIDIA Isaac Sim on Omniverse Cloud

**Cost Calculation**:
- Instance: ~$1.50/hour (spot/on-demand mix)
- Usage: 10 hours/week × 12 weeks = 120 hours
- Storage: ~$25/quarter
- **Total**: ~$205 per quarter per student

### The Latency Trap

:::danger
Controlling a real robot from a cloud instance is dangerous due to latency.

**Solution**: Train in the cloud, download model weights, and flash to local Jetson.
:::

---

## Summary Architecture

Your lab infrastructure should look like this:

| Component | Hardware | Function |
|-----------|----------|----------|
| **Sim Rig** | PC with RTX 4080 + Ubuntu 22.04 | Runs Isaac Sim, Gazebo, Unity, trains models |
| **Edge Brain** | Jetson Orin Nano | Runs inference stack, deploys code |
| **Sensors** | RealSense Camera + LiDAR | Feeds real-world data to AI |
| **Actuator** | Unitree Go2 or G1 (Shared) | Receives motor commands |

---

## Recommendations

### For Budget-Conscious Programs

1. **Shared Workstations**: 1 RTX 4080 workstation per 3-4 students (for simulation)
2. **Individual Edge Kits**: Each student gets a Jetson kit ($700)
3. **Shared Robot**: 1 Unitree Go2 for the entire class

### For Well-Funded Programs

1. **Individual Workstations**: RTX 4090 per student
2. **Individual Edge Kits**: Jetson Orin Nano per student
3. **Multiple Robots**: 2-3 Unitree G1 humanoids for the lab

---

Building a Physical AI lab is a significant investment. Choose between:
- **On-Premise Lab**: High CapEx, no recurring costs
- **Cloud-Native Lab**: Low CapEx, high OpEx (~$200/student/quarter)
