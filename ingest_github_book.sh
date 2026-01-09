#!/bin/bash
# Fetch and ingest book content from GitHub

set -e

REPO_URL="https://raw.githubusercontent.com/HamzaACCA/book-physical-ai-robotics/main"
RAILWAY_URL="https://book-physical-ai-robotics-production.up.railway.app"
ADMIN_KEY="hackathon-admin-key-2024"

echo "📚 Fetching book content from GitHub..."
echo "========================================"
echo ""

# Create combined markdown file
OUTPUT_FILE="physical-ai-robotics-book.md"

# Start with title
cat > $OUTPUT_FILE <<'EOF'
# Physical AI & Humanoid Robotics Course

A comprehensive guide to AI systems in the physical world and embodied intelligence.

EOF

echo "Fetching intro..."
echo "# Introduction" >> $OUTPUT_FILE
curl -s "$REPO_URL/docs/intro.md" | sed '/^---$/,/^---$/d' >> $OUTPUT_FILE
echo -e "\n\n" >> $OUTPUT_FILE

echo "Fetching overview..."
echo "# Course Overview" >> $OUTPUT_FILE
curl -s "$REPO_URL/docs/overview.md" | sed '/^---$/,/^---$/d' >> $OUTPUT_FILE
echo -e "\n\n" >> $OUTPUT_FILE

echo "Fetching hardware requirements..."
echo "# Hardware Requirements" >> $OUTPUT_FILE
curl -s "$REPO_URL/docs/hardware.md" | sed '/^---$/,/^---$/d' >> $OUTPUT_FILE
echo -e "\n\n" >> $OUTPUT_FILE

echo "Fetching weekly breakdown..."
echo "# Weekly Breakdown" >> $OUTPUT_FILE
curl -s "$REPO_URL/docs/weekly-breakdown.md" | sed '/^---$/,/^---$/d' >> $OUTPUT_FILE
echo -e "\n\n" >> $OUTPUT_FILE

echo "Fetching Module 1: ROS 2..."
echo "# Module 1: The Robotic Nervous System (ROS 2)" >> $OUTPUT_FILE
curl -s "$REPO_URL/docs/modules/module1-ros2.md" | sed '/^---$/,/^---$/d' >> $OUTPUT_FILE
echo -e "\n\n" >> $OUTPUT_FILE

echo "Fetching Module 2: Simulation..."
echo "# Module 2: The Digital Twin (Gazebo & Unity)" >> $OUTPUT_FILE
curl -s "$REPO_URL/docs/modules/module2-simulation.md" | sed '/^---$/,/^---$/d' >> $OUTPUT_FILE
echo -e "\n\n" >> $OUTPUT_FILE

echo "Fetching Module 3: Isaac..."
echo "# Module 3: The AI-Robot Brain (NVIDIA Isaac)" >> $OUTPUT_FILE
curl -s "$REPO_URL/docs/modules/module3-isaac.md" | sed '/^---$/,/^---$/d' >> $OUTPUT_FILE
echo -e "\n\n" >> $OUTPUT_FILE

echo "Fetching Module 4: VLA..."
echo "# Module 4: Vision-Language-Action (VLA)" >> $OUTPUT_FILE
curl -s "$REPO_URL/docs/modules/module4-vla.md" | sed '/^---$/,/^---$/d' >> $OUTPUT_FILE
echo -e "\n\n" >> $OUTPUT_FILE

echo "Fetching assessments..."
echo "# Assessments & Projects" >> $OUTPUT_FILE
curl -s "$REPO_URL/docs/assessments.md" | sed '/^---$/,/^---$/d' >> $OUTPUT_FILE
echo -e "\n\n" >> $OUTPUT_FILE

echo ""
echo "✅ Combined book created: $OUTPUT_FILE"
FILE_SIZE=$(wc -c < "$OUTPUT_FILE")
echo "   Size: $((FILE_SIZE / 1024)) KB"
echo ""

# Upload to a temporary location (GitHub gist or use local file server)
echo "📤 Uploading book to GitHub..."

# Create a new file in the repo
BOOK_FILE_URL="$REPO_URL/physical-ai-robotics-book.md"

echo ""
echo "📥 Ingesting book into RAG system..."
echo "   Using file: $OUTPUT_FILE"
echo ""

# Since we have the file locally, we need to make it accessible via URL
# Option 1: Create a GitHub gist
# Option 2: Upload to the repo
# Option 3: Use the combined markdown directly

# For now, let's create the file in the repo
echo "Note: To ingest, you need to either:"
echo "  1. Push this file to GitHub and use the raw URL"
echo "  2. Upload to a file hosting service"
echo "  3. Run ingestion locally with this file"
echo ""
echo "File ready at: $(pwd)/$OUTPUT_FILE"
echo ""
echo "To ingest manually:"
echo ""
echo "# Option 1: Upload file to GitHub first, then:"
echo "curl -X POST $RAILWAY_URL/api/v1/admin/ingest \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -H \"X-Admin-Key: $ADMIN_KEY\" \\"
echo "    -d '{"
echo "        \"file_url\": \"$BOOK_FILE_URL\","
echo "        \"book_title\": \"Physical AI & Humanoid Robotics Course\""
echo "    }'"
echo ""
echo "# Option 2: Run local ingestion (if dependencies installed):"
echo "uv run python -m backend.src.cli.ingest \\"
echo "    --file-path $OUTPUT_FILE \\"
echo "    --book-id $(uuidgen) \\"
echo "    --book-title \"Physical AI & Humanoid Robotics Course\""
