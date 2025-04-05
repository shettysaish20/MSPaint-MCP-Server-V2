import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 10
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_paint_app/mcp_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    # First, let's inspect what a tool object looks like
                    # if tools:
                    #     print(f"First tool properties: {dir(tools[0])}")
                    #     print(f"First tool example: {tools[0]}")
                    
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""You are a math agent with painting skills solving problems in iterations. You have access to various mathematical tools.
                You also have access to a MSPaint application to draw and add your solution to the canvas.

                Available tools:
                {tools_description}

                MSPaint Application information:
                Rectangle co-ordinates: x1 = 763, y1 = 595, x2 = 1788, y2 = 1123


                You must respond with EXACTLY ONE line in one of these formats (no additional text):
                1. For function calls:
                FUNCTION_CALL: function_name|param1|param2|...
                
                2. For final answers:
                FINAL_ANSWER: number

                3. For drawing in Paint:
                USE_PAINT: function_name|param1|param2|...

                4. For completing the task:
                COMPLETE_RUN

                Important:
                - When a function returns multiple values, you need to process all of them
                - Only give FINAL_ANSWER when you have completed all necessary calculations
                - Only USE_PAINT when you are ready to draw in Paint with the FINAL_ANSWER
                - Using paint Steps:
                    - First start the paint application by calling open_paint
                    - Then draw a rectangle using draw_rectangle giving correct parameters
                    - Finally add text using add_text_in_paint with the FINAL_ANSWER: number as text
                    - You must call these functions in the correct order
                - Do not include multiple responses. Give ONE response at a time.
                - Do not include any explanations or additional text.
                - Do not repeat function calls with the same parameters
                - After you have completed the task, you can call COMPLETE_RUN to end the program

                Examples:
                - FUNCTION_CALL: add|5|3
                - FUNCTION_CALL: strings_to_chars_to_int|INDIA
                - FINAL_ANSWER: 42
                - USE_PAINT: draw_rectangle|763|595|1788|1123
                - COMPLETE_RUN

                DO NOT include any explanations or additional text.
                Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER: or USE_PAINT: or COMPLETE_RUN"""

                query = """Return the sum of first 20 Fibonacci numbers."""
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if (line.startswith("FUNCTION_CALL:") or line.startswith("USE_PAINT:")):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break


                    if response_text.startswith("FUNCTION_CALL:") or response_text.startswith("USE_PAINT:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            
                            # Wait longer for Paint to be fully maximized
                            if func_name.startswith("open_paint"):
                                await asyncio.sleep(1)

                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                f"and the function returned {result_str}."
                            )
                            last_response = iteration_result

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Math Agent Execution Complete ===")
                        iteration_response.append(
                                f"In the {iteration + 1} you completed calculations with {response_text}."
                                f"Now call the paint tools starting with USE_PAINT: open_paint"
                                f"Then draw_rectangle with Rectangle co-ordinates followed by add_text_in_paint with the {response_text} as text."
                            )
                        last_response = iteration_result
                        # Commented out the manual call of paint tools
                        # result = await session.call_tool("open_paint")
                        # print(result.content[0].text)

                        # # Wait longer for Paint to be fully maximized
                        # await asyncio.sleep(1)

                        # # Draw a rectangle
                        # ##  Change this for my screen
                        # result = await session.call_tool(
                        #     "draw_rectangle",
                        #     arguments={
                        #         "x1": 763, #780,
                        #         "y1": 595, #380,
                        #         "x2": 1788, #1140,
                        #         "y2": 1123, #700
                        #     }
                        # )
                        # print(result.content[0].text)

                        # # Draw rectangle and add text
                        # result = await session.call_tool(
                        #     "add_text_in_paint",
                        #     arguments={
                        #         "text": response_text
                        #     }
                        # )
                        # print(result.content[0].text)
                        # break
                    elif response_text.startswith("COMPLETE_RUN"):
                        print("\n=== Task complete. Ending run now ===")
                        break

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
