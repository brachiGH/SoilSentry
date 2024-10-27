#!/usr/bin/env python3

import subprocess
import os
import threading

# Path to your virtual environment's activate script
activate_env = "myenv/bin/activate"

# List of Python scripts to run inside the environment
scripts_to_run = [
    "MQTT-broker.py",
    "irrigation_system.py",
    # Add more script paths as needed
]

def run_script_in_env(script):
    """Runs a Python script inside a virtual environment in a separate thread."""
    try:
        # Command to activate the virtual environment and run the script
        if os.name == 'posix':  # Linux/Mac
            command = f"source {activate_env} && python {script}"
        else:  # Windows
            command = f"{activate_env} && python {script}"

        # Use subprocess to execute the command
        result = subprocess.run(command, shell=True, check=True, text=True)
        print(f"Script {script} ran successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error running script {script}: {e}")

def start_jupyter_notebook():
    """Starts a Jupyter notebook inside the virtual environment."""
    try:
        # Command to activate the virtual environment and start Jupyter notebook
        if os.name == 'posix':  # Linux/Mac
            command = f"source {activate_env} && jupyter notebook"
        else:  # Windows
            command = f"{activate_env} && jupyter notebook"

        # Use subprocess to execute the command
        result = subprocess.run(command, shell=True, check=True, text=True)
        print("Jupyter Notebook started successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error starting Jupyter Notebook: {e}")

def main():
    """Main function to run all scripts and start Jupyter Notebook in separate threads."""
    threads = []
    
    # Create threads to run each Python script
    for script in scripts_to_run:
        thread = threading.Thread(target=run_script_in_env, args=(script,))
        threads.append(thread)
        thread.start()

    # Create a thread to start Jupyter Notebook
    jupyter_thread = threading.Thread(target=start_jupyter_notebook)
    threads.append(jupyter_thread)
    jupyter_thread.start()
    
    # Wait for all threads to finish
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
