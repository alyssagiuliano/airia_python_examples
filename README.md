# airia_python_examples
Python examples related to Airia

## Test Harness

**File:** [test_harness.py](test_harness.py)

### What it does
This script automates testing of a pipeline by sending multiple requests with user inputs loaded from text files. It randomly selects from the provided user input files, appends a random suffix to each input (to minimise the effects of model cacheing), and sends it to the pipeline API. The script tracks whether a specific target tool is called during execution and logs all results (including execution IDs, HTTP status codes, and success/failure outcomes) to a timestamped CSV file. This allows for systematic testing and validation of pipeline behavior across multiple iterations.

### Requirements
Before running the test harness, you need to configure the following:

1. **Configuration Variables** (in the script):
   - `PIPELINE_ID`: Your Airia pipeline ID for the agent
   - `API_KEY`: Your Airia API key
   - `USER_ID`: Your Airia user ID
   - `TARGET_TOOL`: Name of the tool you want to ensure is called
   - `LOOP`: Number of execution iterations (default: 10, max: 100)

2. **User Input Files**:
   - `USER_INPUT_FILES`: List of paths to text files containing user inputs
   - Example: `USER_INPUT_FILES = ["input1.txt", "input2.txt", "input3.txt"]`
   - Each file should contain the full user input text that will be sent to the pipeline
   - At least one input file is required

### Output
The script generates a timestamped CSV file (`results_YYYYMMDD_HHMMSS.csv`) containing:
- Iteration number
- Timestamp
- HTTP status code
- Whether the target tool was called
- Tool HTTP status code
- Result (SUCCESS/FAILURE/ERROR)
- Execution ID
