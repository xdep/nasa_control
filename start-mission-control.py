import subprocess
import sys
import asyncio
from nasa_control_panel import main as nasa_main

def start_process(command):
    return subprocess.Popen(command, shell=True)

async def run_nasa_control_panel():
    await nasa_main()

def main():
    print("Initiating NASA Mission Control...")

    # Start the web server
    web_server = start_process(f"{sys.executable} web_server.py")
    print("Web server started.")

    print("\nAll systems are go!")
    print("Open your web browser and navigate to http://localhost:8000 to access the dashboard.")
    print("\nStarting NASA Control Panel simulation...")

    try:
        # Run the NASA Control Panel main function
        asyncio.run(run_nasa_control_panel())
    except KeyboardInterrupt:
        print("\nInitiating shutdown sequence...")
    finally:
        # Terminate the web server process
        web_server.terminate()
        print("All processes terminated. Mission Control shutdown complete.")

if __name__ == "__main__":
    main()