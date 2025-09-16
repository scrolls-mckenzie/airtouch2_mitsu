# AirTouch 2 Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant custom component for controlling Polyaire AirTouch 2 systems with **enhanced Mitsubishi Electric support**.

## ✨ Recent Improvements

- ✅ **Fixed Mitsubishi Electric Support**: Added proper recognition for Gateway ID `0x5`
- ✅ **Crash Prevention**: Fixed crashes when AC reports unknown mode values
- ✅ **Enhanced Stability**: Improved error handling and defensive programming
- ✅ **Better Logging**: More informative error messages and warnings

## Features

- **Climate Control**: Full AC unit control (temperature, mode, fan speed)
- **Zone Management**: Control zone groups and damper positions via fan entities
- **Multi-Brand Support**: Works with various AC brands including:
  - ✅ **Mitsubishi Electric** (now fully supported!)
  - Daikin
  - Fujitsu
  - Samsung
  - And more
- **Real-time Updates**: Live temperature and status monitoring
- **Local Control**: No cloud dependency, works entirely on your local network

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/airtouch2` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

Or use the provided installation script:
```bash
./install.sh /path/to/homeassistant/config
```

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "AirTouch 2"
4. Enter your AirTouch 2 system's IP address
5. Complete the setup

## Entities Created

### Climate Entities
- One climate entity per AC unit
- Control temperature, mode (Heat/Cool/Auto/Dry/Fan), and fan speed
- Real-time temperature monitoring

### Fan Entities  
- One fan entity per zone group
- Control damper position (0-100%)
- Turn zones on/off

## Troubleshooting

### Common Issues

**"Cannot Connect" Error:**
1. Verify your AirTouch 2 system is on the same network as Home Assistant
2. Check the IP address is correct
3. Ensure no firewall is blocking port 8899

**"No AC Units Found" Error:**
1. Wait a few seconds after connecting - the system needs time to discover units
2. Check that your AC units are properly connected to the AirTouch system

**Mitsubishi Electric Units Not Recognized:**
- This integration now includes fixes for Mitsubishi Electric units (Gateway ID 0x5)
- If you still see warnings about unfamiliar gateway IDs, please report them

### Logs
Check Home Assistant logs for detailed error messages:
- Settings → System → Logs
- Look for entries containing "airtouch2"

## Contributing

Issues and pull requests are welcome on the main repository. When reporting issues, please include:
- Your AirTouch system model
- AC unit brand(s)
- Home Assistant version
- Relevant log entries