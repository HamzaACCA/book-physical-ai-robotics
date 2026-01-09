# Book Ingestion Guide

Your RAG chatbot is deployed and working! Now you need to add book content.

## Prerequisites

You need books in **markdown format** with headers to get chapter/section metadata:

```markdown
# Chapter 1: Introduction to Physical AI

This chapter covers the basics...

## What is Physical AI?

Physical AI combines...

## Key Components

The main components are...

# Chapter 2: Hardware Requirements

This chapter discusses...
```

## Option 1: Ingest via Admin API

Use the admin ingestion endpoint from your local machine or WSL:

### Step 1: Prepare Your Book File

Create a markdown file with your book content:

```bash
# Example book structure
cat > physical-ai-book.md <<'EOF'
# Chapter 1: Introduction to Physical AI

Physical AI represents the convergence of artificial intelligence with physical robotics...

## What is Physical AI?

Physical AI is...

## Applications

The main applications include...

# Chapter 2: Hardware Requirements

Modern Physical AI systems require...

## GPU Requirements

For training and inference...

## Sensors and Actuators

Physical AI robots need...
EOF
```

### Step 2: Upload to Accessible Location

Upload your markdown file to a publicly accessible URL:
- GitHub raw URL
- Cloud storage (S3, Google Cloud Storage)
- Any public URL

Example GitHub raw URL:
```
https://raw.githubusercontent.com/username/repo/main/book.md
```

### Step 3: Ingest via API

```bash
curl -X POST https://book-physical-ai-robotics-production.up.railway.app/api/v1/admin/ingest \
    -H "Content-Type: application/json" \
    -H "X-Admin-Key: hackathon-admin-key-2024" \
    -d '{
        "file_url": "https://your-url.com/physical-ai-book.md",
        "book_title": "Physical AI Guide",
        "chunk_size": 800,
        "overlap": 128
    }'
```

**Expected response:**
```json
{
  "status": "success",
  "book_id": "...",
  "chunks_created": 150,
  "embeddings_stored": 150
}
```

### Step 4: Test Your Chatbot

```bash
curl -X POST https://book-physical-ai-robotics-production.up.railway.app/api/v1/chat/message \
    -H "Content-Type: application/json" \
    -d '{"message": "What is Physical AI?"}' | jq .
```

**Expected response with content:**
```json
{
  "answer": "Physical AI represents...",
  "session_id": "...",
  "sources": [
    {
      "chunk_id": "...",
      "text_preview": "Physical AI is...",
      "similarity": 0.85,
      "chapter_title": "Introduction to Physical AI",
      "section_title": "What is Physical AI?"
    }
  ],
  "follow_up_questions": [
    "What are the main applications of Physical AI?",
    "How does Physical AI differ from traditional robotics?",
    "What hardware is required for Physical AI systems?"
  ],
  "retrieval_quality": 0.82
}
```

## Option 2: Ingest from Local Machine (Python CLI)

If you want to run ingestion from your local machine/WSL:

### Step 1: Install Dependencies Locally

```bash
cd /home/hamza/hackathon1

# Install with uv
uv sync

# Or with pip
pip install -e .
```

### Step 2: Set Environment Variables

```bash
export DATABASE_URL="postgresql://neondb_owner:npg_r8MH4dVSPpgJ@ep-patient-tree-adr5pn76-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"
export QDRANT_URL="https://a44bcc35-e2f6-44f0-8a9c-82bb1d13e8f6.us-east4-0.gcp.cloud.qdrant.io"
export QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.b4PSGhupOADwbfNZObErXy0s_hfh9uCiDImu7Y2VpjU"
export QDRANT_COLLECTION_NAME="Hackhaton1"
export GEMINI_API_KEY="AIzaSyDgmhw5VUWVQFlSuqOSrvK8j6cz1FhqapA"
export GEMINI_EMBEDDING_MODEL="models/text-embedding-004"
```

### Step 3: Run Ingestion CLI

```bash
# Generate a book ID
export BOOK_ID=$(uuidgen)

# Ingest the book
python -m backend.src.cli.ingest \
    --file-path ./physical-ai-book.md \
    --book-id $BOOK_ID \
    --book-title "Physical AI Guide" \
    --chunk-size 800 \
    --overlap 128
```

### Step 4: Verify in Database

```bash
python verify_ingestion.py
```

## Sample Book Content

Here's a sample markdown book you can use for testing:

```markdown
# Chapter 1: Introduction to Physical AI

Physical AI represents a revolutionary convergence of artificial intelligence, robotics, and physical systems. Unlike traditional AI that exists purely in software, Physical AI enables machines to perceive, reason about, and interact with the physical world.

## What is Physical AI?

Physical AI combines three key elements:

1. **Perception**: Using sensors to understand the environment
2. **Reasoning**: Processing sensory data to make decisions
3. **Action**: Physically interacting with the world through actuators

This integration allows robots and autonomous systems to operate in unstructured, real-world environments.

## Key Applications

Physical AI is transforming multiple industries:

- **Manufacturing**: Collaborative robots (cobots) working alongside humans
- **Logistics**: Autonomous warehouse robots and delivery systems
- **Healthcare**: Surgical robots and rehabilitation assistants
- **Agriculture**: Autonomous farming equipment
- **Transportation**: Self-driving vehicles

## Historical Context

The journey toward Physical AI began in the 1960s with early industrial robots. However, modern Physical AI leverages advances in:

- Deep learning for perception
- Reinforcement learning for decision-making
- Advanced sensors and actuators
- Edge computing for real-time processing

# Chapter 2: Hardware Requirements

Building Physical AI systems requires specialized hardware components that enable both computation and physical interaction.

## Computing Hardware

### GPU Requirements

Modern Physical AI systems rely heavily on GPUs for:
- Real-time image processing
- Neural network inference
- Sensor fusion algorithms

Recommended specifications:
- NVIDIA RTX 4000 series or higher
- Minimum 8GB VRAM
- CUDA support

### Edge Computing Devices

For mobile robots, edge computing is essential:
- NVIDIA Jetson series (Orin, Xavier)
- Qualcomm Robotics RB5
- Intel NUC with Neural Compute Stick

## Sensors and Actuators

### Vision Systems

- **RGB Cameras**: Standard visual perception
- **Depth Cameras**: 3D environment mapping (e.g., Intel RealSense)
- **LiDAR**: High-precision distance measurement
- **Thermal Cameras**: Temperature-based detection

### Motion Sensors

- IMUs (Inertial Measurement Units)
- Encoders for joint position
- Force/torque sensors
- GPS for outdoor navigation

### Actuators

- **Servo Motors**: Precise position control
- **Stepper Motors**: Incremental motion
- **Pneumatic/Hydraulic**: High-force applications
- **Soft Robotics**: Compliant manipulation

# Chapter 3: Software Architecture

The software stack for Physical AI systems consists of multiple layers working in harmony.

## Operating System Layer

### Robot Operating System (ROS)

ROS is the de facto standard for robotics:
- Modular architecture
- Publisher-subscriber messaging
- Hardware abstraction
- Rich ecosystem of packages

ROS 2 improvements:
- Real-time capabilities
- Better security
- Multi-robot support

## Perception Stack

### Computer Vision

Deep learning models for vision:
- Object detection (YOLO, Faster R-CNN)
- Semantic segmentation
- Instance segmentation
- 3D object recognition

### Sensor Fusion

Combining multiple sensor inputs:
- Kalman filtering
- Particle filters
- Occupancy grid mapping

## Planning and Control

### Motion Planning

Algorithms for path generation:
- RRT (Rapidly-exploring Random Trees)
- A* search
- Trajectory optimization
- MPC (Model Predictive Control)

### Grasp Planning

For manipulation tasks:
- Grasp pose estimation
- Force closure analysis
- Collision avoidance

# Chapter 4: AI Models for Physical Systems

Physical AI leverages various machine learning approaches tailored to embodied agents.

## Reinforcement Learning

RL enables robots to learn through trial and error:

### Model-Free Methods

- Deep Q-Networks (DQN)
- Proximal Policy Optimization (PPO)
- Soft Actor-Critic (SAC)

### Sim-to-Real Transfer

Training in simulation, deploying in reality:
- Domain randomization
- System identification
- Reality gap bridging

## Imitation Learning

Learning from demonstrations:
- Behavioral cloning
- Inverse reinforcement learning
- Learning from human teleoperation

## World Models

Building internal representations:
- Predictive models of dynamics
- Mental simulation for planning
- Counterfactual reasoning

# Chapter 5: Safety and Ethics

As Physical AI systems interact with the real world, safety and ethical considerations are paramount.

## Safety Engineering

### Redundancy and Fail-Safes

- Hardware redundancy
- Software watchdogs
- Emergency stop mechanisms
- Graceful degradation

### Verification and Validation

- Formal verification methods
- Simulation testing
- Hardware-in-the-loop testing
- Field testing protocols

## Ethical Considerations

### Transparency

- Explainable AI for robot decisions
- Audit trails for actions
- Clear communication of capabilities

### Accountability

- Responsibility frameworks
- Liability in case of failures
- Regulatory compliance

### Human-Robot Interaction

- Respecting personal space
- Predictable behavior
- User consent for data collection

# Chapter 6: Future Directions

Physical AI is rapidly evolving. Here are key trends shaping the future.

## Emerging Technologies

### Neuromorphic Computing

Brain-inspired hardware:
- Event-based processing
- Ultra-low power consumption
- Asynchronous operation

### Quantum Sensors

Next-generation perception:
- Quantum magnetometers
- Atomic clocks
- Quantum radar

## Research Frontiers

### Foundation Models for Robotics

Large-scale pre-trained models:
- RT-1, RT-2 (Robotics Transformers)
- Embodied language models
- Cross-embodiment learning

### Soft Robotics

Compliant, adaptive robots:
- Bio-inspired designs
- Variable stiffness materials
- Continuum manipulators

### Swarm Robotics

Collective intelligence:
- Decentralized control
- Emergent behaviors
- Multi-agent coordination

## Industry Outlook

Physical AI is poised for explosive growth:
- Market size projected to reach $100B by 2030
- Increasing adoption across industries
- Integration with IoT and 5G
- Democratization through open-source tools

---

This guide provides a comprehensive overview of Physical AI, from fundamentals to future directions. As the field rapidly evolves, staying current with the latest research and technologies is essential for practitioners and enthusiasts alike.
```

## Verification After Ingestion

### Check Database

```bash
# Check if chunks were created
python verify_ingestion.py
```

### Check Qdrant

```bash
curl -H "api-key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.b4PSGhupOADwbfNZObErXy0s_hfh9uCiDImu7Y2VpjU" \
  https://a44bcc35-e2f6-44f0-8a9c-82bb1d13e8f6.us-east4-0.gcp.cloud.qdrant.io/collections/Hackhaton1
```

### Test Chat Features

Test all enhanced features:

```bash
# Test with ingested content
curl -X POST https://book-physical-ai-robotics-production.up.railway.app/api/v1/chat/message \
    -H "Content-Type: application/json" \
    -d '{"message": "What hardware is needed for Physical AI?"}' | jq .
```

**Expected:**
- ✅ Relevant answer from book content
- ✅ Sources with chapter_title and section_title
- ✅ 3 follow-up questions
- ✅ High retrieval_quality score (>0.7)

## Troubleshooting

### Issue: Ingestion Fails

Check admin API key is correct:
```bash
export ADMIN_API_KEY="hackathon-admin-key-2024"
```

### Issue: No Sources After Ingestion

- Verify chunks were created in PostgreSQL
- Check embeddings in Qdrant collection
- Ensure book content is substantial (not empty)

### Issue: Poor Search Results

- Check embedding quality
- Verify GEMINI_API_KEY is valid
- Test with more specific queries

---

**Ready to ingest books?** Follow Option 1 (Admin API) for the simplest approach!
