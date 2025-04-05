# MSPaint MCP Server with AI-based Planning Algorithms

This project demonstrates how to use Advanced AI Prompting to make LLMs robust to handle complex math problems of multiple steps. It uses the Model Context Protocol (MCP) to allow an AI agent, powered by Google's Gemini model, to interact with a legacy Windows application (MSPaint). The AI agent leverages tools defined using `fastmcp` and implemented with `pywinauto` to solve math problems and then draw the solution on the Paint canvas.

## Table of Contents

- [Introduction](#introduction)
- [Structured Prompting for This Problem Statement](#structured-prompting-for-this-problem-statement)
- [ChatGPT Structured Prompting Evaluation Result](#chatgpt-structured-prompting-evaluation-result)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Key Components](#key-components)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Introduction

This project showcases use of Advanced AI Prompting to make LLM robust to handle complex math problems of multiple steps.


## Structured Prompting for This Problem Statement

```
You are a math agent with painting skills, solving complex math expressions step-by-step.
You have access to various mathematical tools for calculations and verifications, as well as an MSPaint application to draw and present your solution on a canvas.

Available Tools:
{tools_description}

MSPaint Application Information:
- Rectangle coordinates: x1 = 763, y1 = 595, x2 = 1788, y2 = 1123

You must respond with EXACTLY ONE LINE in one of these formats (no additional text):

1. For function calls:
FUNCTION_CALL: {{"name": function_name, "arguments": {{"param1": value1, "param2": value2}}}}

2. For final answers:
FINAL_ANSWER: <NUMBER>

3. For completing the task:
COMPLETE_RUN

Instructions:
- Start by calling the show_reasoning tool ONLY ONCE with a list of all step-by-step reasoning steps explaining how you will solve the problem. Once called, NEVER CALL IT AGAIN UNDER ANY CIRCUMSTANCES.
- When reasoning, tag each step with the reasoning type (e.g., [Arithmetic], [Logical Check]).
- Use all available math tools to solve the problem step-by-step.
- When a function returns multiple values, process all of them.
- Apply BODMAS rules: start with the innermost parentheses and work outward.
- Do not skip steps — perform all calculations sequentially.
- Respond only with one line at a time.
- Call only one tool per response.
- After calculating a number, verify it by calling:
FUNCTION_CALL: {{"name": "verify_calculation", "arguments": {{"expression": <MATH_EXPRESSION>, "expected": <NUMBER>}}}}
- If verify_calculation returns False, re-evaluate your previous steps.
- Once you reach a final answer, check for consistency of all steps and calculations by calling:
FUNCTION_CALL: {{"name": "verify_consistency", "arguments": {{"steps": [[<MATH_EXPRESSION1>, <ANSWER1>], [<MATH_EXPRESSION2>, <ANSWER2>], ...]}}}} 
- If verify_consistency returns False, re-evaluate your previous steps.
- Once verify_consistency return True, submit your final result as:
FINAL_ANSWER: <NUMBER>

Paint Instructions:
- To draw in Paint, follow this sequence strictly:
1. Call open_paint to start the Paint application.
2. Verify Paint is open using verify_paint_open.
3. If verify_paint_open returns False, retry opening Paint until it succeeds.
4. After Paint is open, draw a rectangle using draw_rectangle with correct parameters.
5. Add text using add_text_in_paint, inserting your FINAL_ANSWER: <NUMBER>.

Final Step:
- After completing all calculations, verifications, and drawings, call:
COMPLETE_RUN

Strictly follow the above guidelines.
Your entire response should always be a single line starting with either FUNCTION_CALL:, FINAL_ANSWER: or COMPLETE_RUN.
```

## ChatGPT Structured Prompting Evaluation Result
```json
{
  "explicit_reasoning": true,
  "structured_output": true,
  "tool_separation": true,
  "conversation_loop": true,
  "instructional_framing": true,
  "internal_self_checks": true,
  "reasoning_type_awareness": true,
  "fallbacks": true,
  "overall_clarity": "Extremely strong prompt — it carefully enforces step-by-step reasoning, structured outputs, error handling, and tool use separation. Very minor improvements could be to give a short worked-out example, but even without it, the robustness is excellent."
}
```

## Project Structure

```
├── MSPaint-MCP-Server/
│ ├── mcp_server.py # Defines the MCP server with tools for Paint automation 
│ ├── mcp_client.py # Defines the MCP client that interacts with the server and AI model 
│ ├── requirements.txt # Lists the project dependencies 
│ └── .env # Stores the Gemini API key 
├── README.md # This file
```

## Requirements

- Python 3.11+
- Conda (recommended for environment management)
- Google Gemini API key
- pywin32
- pywinauto
- fastmcp
- python-dotenv
- google-genai
- rich

## Setup

1.  **Create a Conda environment:**

    ```bash
    conda create -n eagenv python=3.11
    conda activate eagenv
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up the Gemini API key:**

    -   Create a `.env` file in the directory.
    -   Add your Gemini API key to the `.env` file:

        ```
        GEMINI_API_KEY=YOUR_API_KEY
        ```

## Usage

1.  **Run the MCP client:**

    ```bash
    python mcp_paint_app/mcp_client.py
    ```

    This will start the MCP client, which connects to the MCP server, initializes the AI agent, and begins the automation process.

## How It Works

1.  **MCP Server (`mcp_server.py`):**
    -   Defines the tools for interacting with MSPaint (e.g., `open_paint`, `draw_rectangle`, `add_text_in_paint`) and various mathematical operations (e.g., `add`, `subtract`, `multiply`, `divide`, `verify_calculation`, `verify_consistency`).
    -   Uses `pywinauto` to control the MSPaint application.
    -   Exposes these tools via the `fastmcp` library.

2.  **MCP Client (`mcp_client.py`):**
    -   Connects to the MCP server.
    -   Uses the Google Gemini model to generate instructions and solve the given math expression.
    -   Parses the model's output to determine which tool to call.
    -   Calls the appropriate tool on the MCP server with the required parameters.
    -   Handles the response from the tool and feeds it back to the model for the next step.
    -   Orchestrates the drawing of the final answer in MSPaint.

3.  **AI Agent (Google Gemini):**
    -   Receives a complex math expression (e.g., `((3000 - (400+552)) / 2 + 1024`).
    -   Uses the available tools (defined in the system prompt) to solve the problem step by step.
    -   Generates function calls (e.g., `FUNCTION_CALL: {"name": "add", "arguments" {"a": 400, "b": 552}}`) to use the tools.
    -   Verifies each calculation using the `verify_calculation` tool.
    -   Ensures the consistency of all steps using the `verify_consistency` tool.
    -   Once the final answer is obtained and verified, it uses Paint to display the result by opening Paint, drawing a rectangle, and adding the final answer as text.
    -   Completes the run by calling the `COMPLETE_RUN` command.


## Key Components

-   **`mcp_server.py`:** Contains the core logic for automating MSPaint. The `open_paint`, `draw_rectangle`, and `add_text_in_paint` functions are the key tools used by the AI agent.
-   **`mcp_client.py`:** Manages the interaction between the AI agent and the MCP server. It sets up the system prompt, calls the tools, and handles the responses.
-   **`requirements.txt`:** Lists all the necessary Python packages for the project.
-   **.env:** Stores the Google Gemini API key.

## Troubleshooting

-   **Permission Issues:** If you encounter permission issues, try running the scripts as an administrator.
-   **Coordinate Issues:** The coordinates used for clicking in MSPaint may need to be adjusted based on your screen resolution and window size. Use the debugging print statements in the code to identify the correct coordinates.
-   **Tool Selection Issues:** If the AI agent is not selecting the correct tools, review the system prompt and ensure that the tool descriptions are accurate.
-   **API Key Issues:** Ensure that your Gemini API key is correctly set in the `.env` file.

## Contributing

Contributions are welcome! Please submit a pull request with your changes.

## License

[MIT License](LICENSE)