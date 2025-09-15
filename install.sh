#!/bin/bash
# Installation script for AirTouch 2 Home Assistant Custom Component

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AirTouch 2 Home Assistant Integration Installer${NC}"
echo "=================================================="

# Check if Home Assistant config directory is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <home-assistant-config-directory>${NC}"
    echo "Example: $0 /config"
    echo "Example: $0 ~/.homeassistant"
    exit 1
fi

HA_CONFIG_DIR="$1"

# Validate Home Assistant config directory
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo -e "${RED}Error: Home Assistant config directory '$HA_CONFIG_DIR' does not exist${NC}"
    exit 1
fi

if [ ! -f "$HA_CONFIG_DIR/configuration.yaml" ]; then
    echo -e "${RED}Error: '$HA_CONFIG_DIR' does not appear to be a Home Assistant config directory${NC}"
    echo "Could not find configuration.yaml"
    exit 1
fi

# Create custom_components directory if it doesn't exist
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
mkdir -p "$CUSTOM_COMPONENTS_DIR"

# Copy the integration
echo "Installing AirTouch 2 integration..."
cp -r "custom_components/airtouch2" "$CUSTOM_COMPONENTS_DIR/"

echo -e "${GREEN}✓ AirTouch 2 integration installed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart Home Assistant"
echo "2. Go to Settings → Devices & Services"
echo "3. Click 'Add Integration'"
echo "4. Search for 'AirTouch 2'"
echo "5. Enter your AirTouch system's IP address"
echo ""
echo -e "${YELLOW}Note: Make sure your AirTouch system is on the same network as Home Assistant${NC}"