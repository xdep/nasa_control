import RPi.GPIO as GPIO
import time
import random
from datetime import datetime, timedelta
import pygame
import os
import asyncio
import json

# Define GPIO pins
CLK1, DIO1 = 17, 18  # 6-digit display
CLK2, DIO2 = 22, 23  # 4-digit display
CLK3, DIO3 = 24, 25  # 4-digit display

# TM1637 commands
ADDR_AUTO = 0x40
ADDR_FIXED = 0x44
STARTADDR = 0xC0

class TM1637:
    def __init__(self, clk, dio):
        self.clk = clk
        self.dio = dio
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk, GPIO.OUT)
        GPIO.setup(self.dio, GPIO.OUT)
        self.brightness = 7  # 0-7

    def start(self):
        GPIO.output(self.dio, GPIO.HIGH)
        GPIO.output(self.clk, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(self.dio, GPIO.LOW)

    def stop(self):
        GPIO.output(self.clk, GPIO.LOW)
        GPIO.output(self.dio, GPIO.LOW)
        time.sleep(0.001)
        GPIO.output(self.clk, GPIO.HIGH)
        GPIO.output(self.dio, GPIO.HIGH)

    def write_byte(self, data):
        for _ in range(8):
            GPIO.output(self.clk, GPIO.LOW)
            GPIO.output(self.dio, data & 1)
            data >>= 1
            GPIO.output(self.clk, GPIO.HIGH)
        
        # Wait for ACK
        GPIO.output(self.clk, GPIO.LOW)
        GPIO.output(self.dio, GPIO.HIGH)
        GPIO.output(self.clk, GPIO.HIGH)
        GPIO.setup(self.dio, GPIO.IN)
        
        while GPIO.input(self.dio):
            time.sleep(0.001)
            if GPIO.input(self.dio):
                break
        
        GPIO.setup(self.dio, GPIO.OUT)

    def display(self, segments):
        self.start()
        self.write_byte(ADDR_AUTO)
        self.stop()
        
        self.start()
        self.write_byte(STARTADDR)
        for seg in segments:
            self.write_byte(seg)
        self.stop()
        
        self.start()
        self.write_byte(0x88 | min(7, max(0, self.brightness)))
        self.stop()

    def encode_char(self, char):
        segments = {
            ' ': 0x00, '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F, '4': 0x66,
            '5': 0x6D, '6': 0x7D, '7': 0x07, '8': 0x7F, '9': 0x6F, '-': 0x40,
            'A': 0x77, 'b': 0x7C, 'C': 0x39, 'd': 0x5E, 'E': 0x79, 'F': 0x71,
            'G': 0x3D, 'H': 0x76, 'I': 0x30, 'J': 0x1E, 'K': 0x76, 'L': 0x38,
            'M': 0x15, 'n': 0x54, 'O': 0x3F, 'P': 0x73, 'q': 0x67, 'r': 0x50,
            'S': 0x6D, 't': 0x78, 'U': 0x3E, 'v': 0x1C, 'W': 0x2A, 'X': 0x76,
            'y': 0x6E, 'Z': 0x5B, '?': 0x53
        }
        return segments.get(char.upper(), 0x00)

    def scroll_text(self, text, delay=0.3):
        padded_text = "      " + text + "      "
        encoded_text = [self.encode_char(char) for char in padded_text]
        
        for i in range(len(padded_text) - 5):
            left_seg = encoded_text[i:i+3]
            right_seg = encoded_text[i+3:i+6]
            display_seg = left_seg[::-1] + right_seg[::-1]
            self.display(display_seg)
            time.sleep(delay)

    def set_brightness(self, level):
        if 0 <= level <= 7:
            self.brightness = level
        else:
            raise ValueError("Brightness must be between 0 and 7")

class EnhancedNASAControlPanel:
    def __init__(self):
        self.display1 = TM1637(CLK1, DIO1)  # 6-digit display
        self.display2 = TM1637(CLK2, DIO2)  # 4-digit display (Altitude)
        self.display3 = TM1637(CLK3, DIO3)  # 4-digit display
        
        # Initialize pygame for audio
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        self.load_sounds()
        
        self.mission_start = None
        self.mission_phases = ["LAUNCH", "ORBIT", "LANDING"]
        self.current_phase = 0
        self.altitude = 0  # Starting altitude in km
        self.velocity = 0
        
        self.alarm_active = False
        self.alarm_messages = ["OXYGN", "ENGNE", "RADAR", "FUEL"]
        
        self.telemetry_data = {
            "FUEL": 100,   # Fuel remaining in %
            "TEMP": 22,    # Temperature in °C
            "RADL": 0.1,   # Radiation level in mSv/h
            "OXGN": 100    # Oxygen level in %
        }
        
        self.crew_members = [
            "ANDR-OK", "MARI-OK", "YURI-OK", "VALK-OK"
        ]
        
        self.orbit_locations = [
            "PACIF", "ASIA", "EUROP", "AFRIC", "ATLNT", "AMER"
        ]
        self.current_location = 0
        
        self.display_mode = 0  # 0: Normal, 1: Crew, 2: Location
        self.simulation_running = False
        self.simulation_speed = 1.0

    def load_sounds(self):
        self.sounds = {
            'beep': self.load_sound('beep'),
            'launch': self.load_sound('launch'),
            'alarm': self.load_sound('alarm'),
            'space_ambience': self.load_sound('space_ambience'),
            'radio_static': self.load_sound('radio_static'),
            'crew_talk': [self.load_sound(f'crew_talk_{i}') for i in range(1, 6)],
            'mission_control': [self.load_sound(f'mission_control_{i}') for i in range(1, 6)],
        }

    def load_sound(self, base_name):
        script_dir = os.path.dirname(os.path.abspath(__file__))
		sounds_dir = os.path.join(script_dir, 'sounds')
        for ext in ['.mp3', '.wav']:
            file_path = os.path.join(script_dir, f'{base_name}{ext}')
            if os.path.exists(file_path):
                try:
                    return pygame.mixer.Sound(file_path)
                except pygame.error:
                    print(f"Error loading {file_path}")
        print(f"Warning: Sound file '{base_name}' not found in MP3 or WAV format.")
        return None

    def play_sound(self, sound_name, loops=0):
        if sound_name in self.sounds:
            sound = self.sounds[sound_name]
            if isinstance(sound, list):
                sound = random.choice(sound)
            if sound:
                sound.play(loops=loops)

    def get_mission_phase(self):
        return self.mission_phases[self.current_phase]

    def get_mission_time(self):
        if self.mission_start:
            elapsed = datetime.now() - self.mission_start
            return f"T+{elapsed.days:03d}:{elapsed.seconds//3600:02d}:{(elapsed.seconds//60)%60:02d}:{elapsed.seconds%60:02d}"
        return "T+000:00:00:00"

    def get_altitude(self):
        return self.altitude

    def get_velocity(self):
        return self.velocity

    def update_telemetry(self, data):
        self.telemetry_data.update(data)

    def start_simulation(self):
        self.simulation_running = True
        self.mission_start = datetime.now()
        self.play_sound('space_ambience', -1)  # Start ambient sound

    def pause_simulation(self):
        self.simulation_running = False
        pygame.mixer.pause()

    def stop_simulation(self):
        self.simulation_running = False
        self.mission_start = None
        pygame.mixer.stop()
        self.reset_simulation_data()

    def reset_simulation_data(self):
        self.current_phase = 0
        self.altitude = 0
        self.velocity = 0
        self.telemetry_data = {
            "FUEL": 100, "TEMP": 22, "RADL": 0.1, "OXGN": 100
        }

    def set_simulation_speed(self, speed):
        self.simulation_speed = speed

    def update_mission_phase(self):
        if random.random() < 0.01 * self.simulation_speed:
            self.current_phase = min(self.current_phase + 1, len(self.mission_phases) - 1)

    def update_telemetry(self):
        self.telemetry_data["FUEL"] = max(0, self.telemetry_data["FUEL"] - random.uniform(0, 0.1) * self.simulation_speed)
        self.telemetry_data["TEMP"] += random.uniform(-0.5, 0.5) * self.simulation_speed
        self.telemetry_data["RADL"] = max(0, self.telemetry_data["RADL"] + random.uniform(-0.01, 0.02) * self.simulation_speed)
        self.telemetry_data["OXGN"] = max(0, min(100, self.telemetry_data["OXGN"] + random.uniform(-0.1, 0.1) * self.simulation_speed))

    def update_altitude_velocity(self):
        if self.current_phase == 0:  # LAUNCH
            self.altitude += random.uniform(0.1, 0.5) * self.simulation_speed
            self.velocity += random.uniform(0.1, 0.3) * self.simulation_speed
        elif self.current_phase == 1:  # ORBIT
            self.altitude += random.uniform(-0.1, 0.1) * self.simulation_speed
            self.velocity = 7.8  # Orbital velocity
        else:  # LANDING
            self.altitude = max(0, self.altitude - random.uniform(0.1, 0.3) * self.simulation_speed)
            self.velocity = max(0, self.velocity - random.uniform(0.1, 0.2) * self.simulation_speed)

    def check_alarms(self):
        self.alarm_active = (self.telemetry_data["FUEL"] < 20 or 
                             self.telemetry_data["OXGN"] < 80 or 
                             self.telemetry_data["RADL"] > 0.5)
        if self.alarm_active:
            self.play_sound('alarm')

    def update_orbit_location(self):
        if random.random() < 0.1 * self.simulation_speed:
            self.current_location = (self.current_location + 1) % len(self.orbit_locations)

    def update_displays(self):
        if self.alarm_active:
            self.display_alarm()
        elif self.display_mode == 0:
            self.display_normal()
        elif self.display_mode == 1:
            self.display_crew()
        elif self.display_mode == 2:
            self.display_location()
        
        self.display_altitude()
        self.display_velocity()

    def display_normal(self):
        self.display1.scroll_text(self.get_mission_time(), delay=0.2)

    def display_altitude(self):
        alt_str = f"{int(self.altitude):04d}"
        self.display2.display([self.display2.encode_char(c) for c in alt_str])

    def display_velocity(self):
        vel_str = f"{self.velocity:.2f}"[:4].rjust(4)
        self.display3.display([self.display3.encode_char(c) for c in vel_str])

    def display_alarm(self):
        alarm_msg = random.choice(self.alarm_messages)
        self.display1.scroll_text("ALERT " + alarm_msg, delay=0.2)

    def display_crew(self):
        crew_member = self.crew_members[self.display_mode % len(self.crew_members)]
        self.display1.scroll_text("CREW " + crew_member, delay=0.2)

    def display_location(self):
        location = self.orbit_locations[self.current_location]
        self.display1.scroll_text("LOC " + location, delay=0.2)

    async def run(self):
        try:
            while True:
                if self.simulation_running:
                    self.update_mission_phase()
                    self.update_telemetry()
                    self.update_altitude_velocity()
                    self.check_alarms()
                    self.update_orbit_location()
                    self.update_displays()

                    if random.random() < 0.1 * self.simulation_speed:
                        self.play_sound('radio_static')
                        await asyncio.sleep(0.5)
                        if random.choice([True, False]):
                            self.play_sound('crew_talk')
                        else:
                            self.play_sound('mission_control')
                        await asyncio.sleep(2)
                        self.play_sound('radio_static')

                await asyncio.sleep(1 / self.simulation_speed)
        except KeyboardInterrupt:
            print("\nSimulation stopped")
        finally:
            pygame.mixer.quit()
            GPIO.cleanup()

control_panel = EnhancedNASAControlPanel()

async def handle_websocket_message(message):
    data = json.loads(message)
    command = data.get('command')

    if command == 'get_status':
        return json.dumps({
            'missionPhase': control_panel.get_mission_phase(),
            'missionTime': control_panel.get_mission_time(),
            'altitude': control_panel.get_altitude(),
            'velocity': control_panel.get_velocity(),
            'telemetry': control_panel.telemetry_data,
            'alarmActive': control_panel.alarm_active,
            'orbitLocation': control_panel.orbit_locations[control_panel.current_location]
        })
    elif command == 'start_simulation':
        control_panel.start_simulation()
    elif command == 'pause_simulation':
        control_panel.pause_simulation()
    elif command == 'stop_simulation':
        control_panel.stop_simulation()
    elif command == 'set_simulation_speed':
        control_panel.set_simulation_speed(float(data['speed']))
    elif command == 'update_telemetry':
        control_panel.update_telemetry(data['telemetry'])
    elif command == 'trigger_alarm':
        control_panel.alarm_active = True
    elif command == 'silence_alarm':
        control_panel.alarm_active = False
    elif command == 'play_sound':
        control_panel.play_sound(data['sound'])
    elif command == 'set_display_mode':
        control_panel.display_mode = int(data['mode'])
    elif command == 'set_display_brightness':
        brightness = int(data['brightness'])
        control_panel.display1.set_brightness(brightness)
        control_panel.display2.set_brightness(brightness)
        control_panel.display3.set_brightness(brightness)
    else:
        return json.dumps({'error': 'Unknown command'})

    return json.dumps({'success': True})

async def websocket_server(websocket, path):
    try:
        async for message in websocket:
            response = await handle_websocket_message(message)
            await websocket.send(response)
    except websockets.exceptions.ConnectionClosed:
        pass

async def main():
    server = await websockets.serve(websocket_server, "localhost", 8000)
    control_panel_task = asyncio.create_task(control_panel.run())
    
    print("NASA Control Panel Simulation started")
    print("WebSocket server running on ws://localhost:8000")
    
    try:
        await asyncio.gather(server.wait_closed(), control_panel_task)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    import websockets
    asyncio.run(main())
else:
    import websockets