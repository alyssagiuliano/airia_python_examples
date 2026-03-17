"""
Test Harness for Pipeline Execution Testing

This script automates testing of a pipeline by sending multiple requests with user inputs
loaded from text files. It randomly selects from the provided user input files, appends a
random suffix to each input (to minimise the effects of model cacheing), and sends it to the 
pipeline API. The script tracks whether a specific target tool is called during execution and 
logs all results (including execution IDs, HTTP status codes, and success/failure outcomes) 
to a timestamped CSV file. This allows for systematic testing and validation of pipeline 
behaviour across multiple iterations.
"""

import requests
import os
import csv
import random
import string
import sys
from datetime import datetime

PIPELINE_ID = "" # Enter pipeline id here
API_KEY = "" # Enter api key here
USER_ID = "" # Enter user id here
USER_INPUT_FILES = []  # Add your file paths here -  Example: USER_INPUT_FILES = ["input1.txt", "input2.txt", "input3.txt"]
TARGET_TOOL = "" # Enter name for tool you want to ensure is called here 
LOOP = 10 # Modify execution iterations here

def load_user_inputs_from_files(file_paths):
    """Load user inputs from one or more text files."""
    user_inputs = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        with open(file_path, 'r') as f:
            content = f.read().strip()
            if content:
                user_inputs.append(content)
            else:
                print(f"Warning: File is empty: {file_path}")

    if not user_inputs:
        print("Error: No user inputs loaded from the provided files.")
        sys.exit(1)

    return user_inputs

if not USER_INPUT_FILES:
    print("Error: Please specify at least one user input file in USER_INPUT_FILES")
    print("Example: USER_INPUT_FILES = ['input1.txt', 'input2.txt']")
    sys.exit(1)

USER_INPUTS = load_user_inputs_from_files(USER_INPUT_FILES)
print(f"Loaded {len(USER_INPUTS)} user input(s) from files")

url = f"https://prodaus.api.airia.ai/v1/PipelineExecution/{PIPELINE_ID}"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}


def run(iteration):
    selected_input = random.choice(USER_INPUTS)
    random_suffix = "".join(random.choices(string.ascii_lowercase, k=2))
    user_input_with_suffix = selected_input + random_suffix

    payload = {
        "userInput": user_input_with_suffix,
        "debug": True,
        "userId": USER_ID,
        "includeToolsResponse": True
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        http_status = response.status_code
        print(f"\nStatus: {http_status}")

        # Try to parse JSON response
        try:
            post_data = response.json()
        except ValueError:
            print(f"Error: Unable to parse JSON response")
            return {
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "http_status": http_status,
                "tool_called": False,
                "tool_http_status": "N/A",
                "result": "ERROR",
                "execution_id": "N/A"
            }

        execution_id = post_data.get("executionId", "N/A")
        report = post_data.get("report", {})

        snow_tool_found = False
        result = None
        tool_http_status = None

        for step_id, step in report.items():
            tools = step.get("debugInformation", {}).get("tools", [])
            for tool in tools:
                tool_name = tool.get("ToolName", "Unknown Tool")
                if tool_name == TARGET_TOOL:
                    snow_tool_found = True
                    tool_http_status = tool.get("ResponseStatusCode")
                    if tool_http_status == 200:
                        result = "SUCCESS"
                        print(f"\nResult: SUCCESS ('{TARGET_TOOL}' called, HTTP {tool_http_status})")
                    else:
                        result = "FAILURE"
                        print(f"\nResult: FAILURE ('{TARGET_TOOL}' called, HTTP {tool_http_status})")
                        print(f"Execution ID: {execution_id}")

        if not snow_tool_found:
            result = "FAILURE"
            print(f"\nResult: FAILURE ('{TARGET_TOOL}' was not called)")
            print(f"Execution ID: {execution_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error: Request failed - {e}")
        return {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "http_status": "N/A",
            "tool_called": False,
            "tool_http_status": "N/A",
            "result": "ERROR",
            "execution_id": "N/A"
        }

    return {
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "http_status": http_status,
        "tool_called": snow_tool_found,
        "tool_http_status": tool_http_status if snow_tool_found else "N/A",
        "result": result,
        "execution_id": execution_id
    }


script_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(script_dir, f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
loop = min(LOOP, 100)

fieldnames = ["iteration", "timestamp", "http_status", "tool_called", "tool_http_status", "result", "execution_id"]

with open(output_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for i in range(loop):
        print(f"\n--- Iteration {i + 1} of {loop} ---")
        row = run(i + 1)
        writer.writerow(row)

print(f"\nResults saved to {output_file}")
