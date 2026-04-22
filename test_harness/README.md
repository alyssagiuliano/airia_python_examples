# Test Harness

Automates testing of an Airia pipeline by sending multiple requests with user inputs loaded from text files. Randomly selects from the provided input files, appends a random suffix to each input (to minimise the effects of model caching), and sends it to the pipeline API. Tracks whether a specific target tool is called during execution and logs all results to a timestamped CSV file.

## Configuration

Edit the constants at the top of `test_harness.py`:

| Variable | Description |
|---|---|
| `PIPELINE_ID` | Your Airia pipeline ID |
| `API_KEY` | Your Airia API key |
| `USER_ID` | Your Airia user ID |
| `TARGET_TOOL` | Name of the tool you want to verify is called |
| `LOOP` | Number of iterations (default: 10, max: 100) |
| `USER_INPUT_FILES` | List of paths to `.txt` files containing user inputs |

Each text file in `USER_INPUT_FILES` should contain one complete user input. At least one file is required.

## Usage

```bash
python test_harness.py
```

## Output

Generates a timestamped CSV file (`results_YYYYMMDD_HHMMSS.csv`) in the same directory containing:

| Column | Description |
|---|---|
| `iteration` | Iteration number |
| `timestamp` | ISO timestamp of the request |
| `http_status` | HTTP status code from the pipeline API |
| `tool_called` | Whether the target tool was called |
| `tool_http_status` | HTTP status returned by the tool |
| `result` | `SUCCESS`, `FAILURE`, or `ERROR` |
| `execution_id` | Pipeline execution ID for tracing |

## Dependencies

```
requests
```
