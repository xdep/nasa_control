# NASA Control Panel Simulation

## Overview
This project simulates a NASA Control Panel using a Raspberry Pi 2 and three LED displays. It provides a web-based dashboard for monitoring and controlling the simulation.

## Hardware Requirements
- Raspberry Pi 2
- 3x TM1637 LED Displays
- Necessary jumper wires

## Pin Configuration
The project uses the following GPIO pins on the Raspberry Pi 2 for the three TM1637 LED displays:

| Display | CLK Pin | DIO Pin |
|---------|---------|---------|
| Display 1 (6-digit) | GPIO 17 | GPIO 18 |
| Display 2 (4-digit) | GPIO 22 | GPIO 23 |
| Display 3 (4-digit) | GPIO 24 | GPIO 25 |

Make sure to connect the VCC and GND of each display to the appropriate power and ground pins on the Raspberry Pi.

## Software Prerequisites
- Python 3.7+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/nasa-control-panel.git
   cd nasa-control-panel
   ```

2. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up the service:
   ```
   sudo ./install_nasa_control_panel_service.sh
   ```
   Follow the prompts to configure the service.

## Usage

### Starting the Simulation
The simulation should start automatically as a service. If it doesn't:

1. Start the service:
   ```
   sudo systemctl start nasa-control-panel.service
   ```

2. Check the status:
   ```
   sudo systemctl status nasa-control-panel.service
   ```

### Accessing the Dashboard
Open a web browser and navigate to:
```
http://[Raspberry_Pi_IP]:8000
```
Replace `[Raspberry_Pi_IP]` with the IP address of your Raspberry Pi.

### Controlling the Simulation
Use the web dashboard to:
- Start, pause, and stop the simulation
- Adjust telemetry data
- Trigger alarms
- Control audio playback
- Change display modes and brightness

## File Structure
- `nasa_control_panel.py`: Main simulation script
- `start_mission_control.py`: Script to start all components
- `web_server.py`: Simple HTTP server for the dashboard
- `dashboard.html`: Web-based control panel
- `sounds/`: Directory containing audio files
- `install_nasa_control_panel_service.sh`: Service installation script

## Troubleshooting

1. If the service fails to start, check the logs:
   ```
   sudo journalctl -u nasa-control-panel.service
   ```

2. Ensure all GPIO pins are correctly connected.

3. Verify that the `sounds/` directory contains all necessary audio files.

## Contributing
Contributions to improve the simulation are welcome. Please submit a pull request or open an issue to discuss proposed changes.

## License
GNU 

