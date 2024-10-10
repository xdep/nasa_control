import asyncio
import websockets
import json
from nasa_control_panel import NASAControlPanel

control_panel = NASAControlPanel()

async def handle_websocket(websocket, path):
    try:
        async for message in websocket:
            data = json.loads(message)
            command = data['command']
            
            if command == 'get_status':
                status = {
                    'missionPhase': control_panel.get_mission_phase(),
                    'missionTime': control_panel.get_mission_time(),
                    'altitude': control_panel.get_altitude(),
                    'velocity': control_panel.get_velocity()
                }
                await websocket.send(json.dumps(status))
            
            elif command == 'update_telemetry':
                control_panel.update_telemetry(data['telemetry'])
                await websocket.send(json.dumps({'success': True}))
            
            # Add more command handlers as needed
    
    except websockets.exceptions.ConnectionClosed:
        pass

start_server = websockets.serve(handle_websocket, "localhost", 8000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
