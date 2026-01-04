---
sidebar_position: 7
---

# Assessments

This course uses **project-based assessments** to evaluate your mastery of Physical AI concepts. Each assessment builds on previous modules and culminates in a comprehensive capstone project.

---

## Assessment 1: ROS 2 Package Development (20%)

**Due**: End of Week 5

### Objective
Demonstrate understanding of ROS 2 fundamentals by building a multi-node robotic system.

### Requirements

1. **Publisher-Subscriber System**:
   - Create at least 3 nodes communicating via topics
   - Implement custom message types
   - Handle sensor data (simulated or real)

2. **Service Integration**:
   - Implement at least 1 service for configuration or control
   - Demonstrate request-response pattern

3. **Launch File**:
   - Create a launch file that starts all nodes
   - Include parameter configuration
   - Add proper namespacing

4. **Documentation**:
   - README with installation and usage instructions
   - Code comments explaining architecture
   - ROS graph visualization (rqt_graph)

### Evaluation Criteria

| Criterion | Points |
|-----------|--------|
| Code Quality | 25% |
| Functionality | 40% |
| Documentation | 20% |
| ROS 2 Best Practices | 15% |

---

## Assessment 2: Gazebo Simulation Implementation (20%)

**Due**: End of Week 7

### Objective
Create a realistic simulation environment for robot testing and development.

### Requirements

1. **Robot Model**:
   - Design a URDF/SDF robot model
   - Include at least 5 joints
   - Add visual and collision geometries

2. **Sensor Integration**:
   - Add at least 2 different sensor types (LiDAR, camera, IMU)
   - Visualize sensor data in RViz
   - Publish sensor data to ROS 2 topics

3. **World Design**:
   - Create a custom Gazebo world with obstacles
   - Include interactive objects
   - Configure physics parameters (gravity, friction)

4. **Integration**:
   - Launch robot in Gazebo via ROS 2 launch file
   - Demonstrate teleoperation or autonomous movement
   - Record simulation footage

### Evaluation Criteria

| Criterion | Points |
|-----------|--------|
| Robot Model Quality | 30% |
| Sensor Implementation | 30% |
| World Design | 20% |
| ROS 2 Integration | 20% |

---

## Assessment 3: Isaac-Based Perception Pipeline (20%)

**Due**: End of Week 10

### Objective
Build an AI-powered perception system using NVIDIA Isaac.

### Requirements

1. **VSLAM Implementation**:
   - Set up Isaac ROS VSLAM
   - Generate a map of a simulated environment
   - Demonstrate localization accuracy

2. **Object Detection**:
   - Implement real-time object detection
   - Use Isaac Sim for synthetic data generation
   - Achieve above 80% detection accuracy on test objects

3. **Navigation Integration**:
   - Integrate VSLAM with Nav2
   - Demonstrate autonomous navigation to goal positions
   - Handle dynamic obstacles

4. **Performance Optimization**:
   - Profile GPU usage and latency
   - Optimize for real-time performance (above 15 FPS)
   - Deploy to Jetson hardware (if available)

### Evaluation Criteria

| Criterion | Points |
|-----------|--------|
| VSLAM Quality | 25% |
| Object Detection Accuracy | 30% |
| Navigation Performance | 25% |
| Optimization | 20% |

---

## Capstone Project: Simulated Humanoid with Conversational AI (40%)

**Due**: End of Week 13 (Final Presentations)

### Objective
Design and deploy an autonomous humanoid robot capable of understanding voice commands, planning actions, navigating environments, and manipulating objects—all in a simulated environment.

### Project Scenario

**User Command**: "Go to the kitchen and bring me a cup"

**Robot Must**:
1. ✅ Recognize the voice command (Whisper)
2. ✅ Plan a sequence of actions (GPT-4/LLM)
3. ✅ Navigate to the kitchen (Nav2 + VSLAM)
4. ✅ Detect and locate the cup (Isaac ROS perception)
5. ✅ Pick up the cup (Manipulation controller)
6. ✅ Navigate back to the user
7. ✅ Hand off the cup

### Technical Requirements

#### 1. Speech-to-Action (15%)
- Implement OpenAI Whisper for speech recognition
- Parse voice commands into structured intents
- Handle clarification requests

#### 2. Cognitive Planning (20%)
- Use an LLM (GPT-4, Claude, or open-source) to plan actions
- Convert natural language to ROS 2 action sequences
- Handle failure recovery

#### 3. Navigation (20%)
- Implement Nav2 path planning
- Integrate VSLAM for localization
- Avoid static and dynamic obstacles

#### 4. Perception (20%)
- Object detection and classification
- 3D pose estimation
- Real-time processing (less than 500ms latency)

#### 5. Manipulation (15%)
- Humanoid hand control
- Grasp planning and execution
- Force-sensitive grasping

#### 6. System Integration (10%)
- All components work together seamlessly
- Proper error handling and logging
- Clean code architecture

### Deliverables

1. **Working Demo** (40%):
   - Live demonstration during final week
   - Video recording of successful execution
   - Handle at least 3 different voice commands

2. **Technical Documentation** (25%):
   - System architecture diagram
   - Component descriptions and interfaces
   - Setup and deployment instructions
   - Known limitations and future improvements

3. **Code Repository** (20%):
   - Clean, well-structured code
   - README with installation steps
   - Example usage and test cases
   - ROS 2 package structure

4. **Presentation** (15%):
   - 10-minute presentation to class
   - Slides explaining design decisions
   - Q&A session
   - Reflection on challenges and learnings

### Evaluation Rubric

| Component | Excellent (90-100%) | Good (80-89%) | Satisfactory (70-79%) | Needs Improvement (below 70%) |
|-----------|---------------------|---------------|----------------------|------------------------|
| **Voice Recognition** | 95% or higher accuracy, handles noise | 85-94% accuracy | 70-84% accuracy | below 70% accuracy |
| **Action Planning** | Optimal plans, handles edge cases | Good plans, some edge cases | Basic plans work | Plans often fail |
| **Navigation** | Smooth, optimal paths | Good paths, minor issues | Reaches goal with retries | Frequent failures |
| **Perception** | above 90% detection, robust | 80-90% detection | 70-80% detection | below 70% detection |
| **Manipulation** | Smooth grasps, no drops | Occasional retries needed | Multiple attempts | Frequent failures |
| **Integration** | Seamless, production-ready | Minor integration issues | Works with manual intervention | Components don't integrate |

---

## Grading Breakdown

| Assessment | Weight |
|------------|--------|
| ROS 2 Package Development | 20% |
| Gazebo Simulation Implementation | 20% |
| Isaac Perception Pipeline | 20% |
| **Capstone Project** | **40%** |
| **Total** | **100%** |

---

## Academic Integrity

- All code must be your own or properly attributed
- You may use open-source libraries and frameworks
- Collaboration is encouraged, but submissions must be individual
- Generative AI (ChatGPT, Copilot) can be used for assistance, but you must understand and be able to explain all code

---

## Late Submission Policy

- **1-2 days late**: 10% penalty
- **3-5 days late**: 25% penalty
- **More than 5 days late**: 50% penalty
- **Capstone project**: No late submissions accepted (due to presentation requirement)

---

## Resources

- **Office Hours**: Weekly sessions for technical support
- **Discussion Forum**: Slack/Discord for peer collaboration
- **Documentation**: ROS 2, Isaac, Gazebo official docs
- **Hardware Lab**: Access to workstations and robots (schedule required)
