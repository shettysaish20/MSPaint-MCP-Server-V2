# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import re
import os
import sys
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics

# instantiate an MCP server client
console = Console()
mcp = FastMCP("AdvancedCalculator")

# DEFINE TOOLS

## Session 5 Assignment additional tools
@mcp.tool()
def show_reasoning(steps: list) -> dict:
    """Show the step-by-step reasoning process"""
    console.print("[blue]FUNCTION CALL:[/blue] show_reasoning()")
    for i, step in enumerate(steps, 1):
        console.print(Panel(
            f"{step}",
            title=f"Step {i}",
            border_style="cyan"
        ))
    return {
        "content": [TextContent(
        type="text",
        text="REASONING SHOWN. FOLLOW THIS INSTRUCTION STRICTLY. PROCEED FURTHER. DO NOT CALL THIS TOOL AGAIN! YOU HAVE CALLED IT ONCE! DO NOT REPEAT THIS TOOL CALL! I REPEAT, DO NOT CALL THIS FUNTCION AGAIN!"
    )]
    }

# @mcp.tool()
# def calculate(expression: str) -> TextContent:
#     """Calculate the result of an expression"""
#     console.print("[blue]FUNCTION CALL:[/blue] calculate()")
#     console.print(f"[blue]Expression:[/blue] {expression}")
#     try:
#         result = eval(expression)
#         console.print(f"[green]Result:[/green] {result}")
#         return TextContent(
#             type="text",
#             text=str(result)
#         )
#     except Exception as e:
#         console.print(f"[red]Error:[/red] {str(e)}")
#         return TextContent(
#             type="text",
#             text=f"Error: {str(e)}"
#         )

## Added new tool to verify if paint app is open
@mcp.tool()
def verify_paint_open() -> dict:
    """Verify if Paint is open"""
    global paint_app
    if paint_app:
        console.print("[green]Paint is open![/green]")
        return {"content": TextContent(
            type="text",
            text="TRUE: Paint is open! Proceed with the next step. Do not generate any additional text."
        )
        }
    else:
        console.print("[red]Paint is not open![/red]")
        return {"content": [TextContent(
            type="text",
            text="FALSE: Paint is not open! Try opening it again. Do not generate any additional text."
        )]
        }


@mcp.tool()
def verify_calculation(expression: str, expected: float) -> dict:
    """Verify if a calculation is correct"""
    console.print("[blue]FUNCTION CALL:[/blue] verify()")
    console.print(f"[blue]Verifying:[/blue] {expression} = {expected}")
    try:
        actual = float(eval(expression))
        is_correct = abs(actual - float(expected)) < 1e-10
        
        if is_correct:
            console.print(f"[green] Correct! {expression} = {expected}[/green]")
        else:
            console.print(f"[red] Incorrect! {expression} should be {actual}, got {expected}[/red]")
            
        return {"content": [TextContent(
            type="text",
            text=str(is_correct)
        )]
        }
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return {"content": [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
        }

@mcp.tool()
def verify_consistency(steps: list) -> TextContent:
    """Check if calculation steps are consistent with each other"""
    # console.print("[blue]FUNCTION CALL:[/blue] check_consistency()")
    
    try:
        # Create a table for step analysis
        # table = Table(
        #     title="Step-by-Step Consistency Analysis",
        #     box=box.ROUNDED,
        #     show_header=True,
        #     header_style="bold cyan"
        # )
        # table.add_column("Step", style="cyan")
        # table.add_column("Expression", style="blue")
        # table.add_column("Result", style="green")
        # table.add_column("Checks", style="yellow")

        issues = []
        warnings = []
        insights = []
        previous = None
        
        for i, (expression, result) in enumerate(steps, 1):
            print("Checking step:", i)
            checks = []
            
            # 1. Basic Calculation Verification
            try:
                expected = eval(expression)
                if abs(float(expected) - float(result)) < 1e-10:
                    checks.append("[green] Calculation verified[/green]")
                else:
                    issues.append(f"Step {i}: Calculation mismatch")
                    checks.append("[red] Calculation error[/red]")
            except:
                warnings.append(f"Step {i}: Couldn't verify calculation")
                checks.append("[yellow] Verification failed[/yellow]")

            # 2. Dependency Analysis
            if previous:
                prev_expr, prev_result = previous
                if str(prev_result) in expression:
                    checks.append("[green] Uses previous result[/green]")
                    insights.append(f"Step {i} builds on step {i-1}")
                else:
                    checks.append("[blue] Independent step[/blue]")

            # 3. Magnitude Check
            if previous and result != 0 and previous[1] != 0:
                ratio = abs(result / previous[1])
                if ratio > 1000:
                    warnings.append(f"Step {i}: Large increase ({ratio:.2f}x)")
                    checks.append("[yellow] Large magnitude increase[/yellow]")
                elif ratio < 0.001:
                    warnings.append(f"Step {i}: Large decrease ({1/ratio:.2f}x)")
                    checks.append("[yellow] Large magnitude decrease[/yellow]")

            # 4. Pattern Analysis
            operators = re.findall(r'[\+\-\*\/\(\)]', expression)
            if '(' in operators and ')' not in operators:
                warnings.append(f"Step {i}: Mismatched parentheses")
                checks.append("[red] Invalid parentheses[/red]")

            # 5. Result Range Check
            if abs(result) > 1e6:
                warnings.append(f"Step {i}: Very large result")
                checks.append("[yellow] Large result[/yellow]")
            elif abs(result) < 1e-6 and result != 0:
                warnings.append(f"Step {i}: Very small result")
                checks.append("[yellow] Small result[/yellow]")

            # Add row to table
            # table.add_row(
            #     f"Step {i}",
            #     expression,
            #     f"{result}",
            #     "\n".join(checks)
            # )
            
            previous = (expression, result)

        # Display Analysis
        # console.print("\n[bold cyan]Consistency Analysis Report[/bold cyan]")
        # console.print(table)

        # if issues:
        #     console.print(Panel(
        #         "\n".join(f"[red]• {issue}[/red]" for issue in issues),
        #         title="Critical Issues",
        #         border_style="red"
        #     ))

        # if warnings:
        #     console.print(Panel(
        #         "\n".join(f"[yellow]• {warning}[/yellow]" for warning in warnings),
        #         title="Warnings",
        #         border_style="yellow"
        #     ))

        # if insights:
        #     console.print(Panel(
        #         "\n".join(f"[blue]• {insight}[/blue]" for insight in insights),
        #         title="Analysis Insights",
        #         border_style="blue"
        #     ))

        # Final Consistency Score
        total_checks = len(steps) * 5  # 5 types of checks per step
        passed_checks = total_checks - (len(issues) * 2 + len(warnings))
        consistency_score = (passed_checks / total_checks) * 100

        # console.print(Panel(
        #     f"[bold]Consistency Score: {consistency_score:.1f}%[/bold]\n" +
        #     f"Passed Checks: {passed_checks}/{total_checks}\n" +
        #     f"Critical Issues: {len(issues)}\n" +
        #     f"Warnings: {len(warnings)}\n" +
        #     f"Insights: {len(insights)}",
        #     title="Summary",
        #     border_style="green" if consistency_score > 80 else "yellow" if consistency_score > 60 else "red"
        # ))

        return TextContent(
            type="text",
            text=str({
                "consistency_score": consistency_score,
                "issues": issues,
                "warnings": warnings,
                "insights": insights,
                "result": True if consistency_score > 80 else False,
                "next_step": "Return the final result as FINAL_ANSWER: <NUMBER>" if consistency_score > 80 else "Please review the steps and try again."
            })
        )
    except Exception as e:
        console.print(f"[red]Error in consistency check: {str(e)}[/red]")
        return TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )


#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]


@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Get primary monitor width to adjust coordinates
        primary_width = GetSystemMetrics(0)
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.2)
        
        # Click on the Rectangle tool using the correct coordinates for secondary screen
        paint_window.click_input(coords=(797, 128 )) ##  change for my screen
        time.sleep(0.2)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')

        # Log canvas position and size for debugging
        canvas_rect = canvas.rectangle()
        print(f"Canvas Rectangle: {canvas_rect}")

        # Draw rectangle - coordinates should be relative to the Paint window
        # No need to add primary_width since we're clicking within the Paint window
        print(f"Clicking at: ({x1}, {y1})")
        canvas.click_input(coords=(x1, y1))
        time.sleep(0.1)

        print(f"Pressing mouse at: ({x1}, {y1})")
        canvas.press_mouse_input(coords=(x1, y1))
        time.sleep(0.1)

        print(f"Releasing mouse at: ({x2}, {y2})")
        canvas.release_mouse_input(coords=(x2, y2))
        time.sleep(0.1)

        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2}). Proceed with the next step. Do not generate any additional text."
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}. Retry this step."
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # # Click on the Rectangle tool
        # paint_window.click_input(coords=(797, 128 )) ##  Change co-ordinates for my screen 
        # time.sleep(0.5) 
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Select text tool using keyboard shortcuts
        paint_window.type_keys('t')
        time.sleep(0.5)
        paint_window.type_keys('x')
        time.sleep(0.5)
        
        # Click where to start typing
        canvas.click_input(coords=(1025, 923))
        time.sleep(0.5)
        
        # Type the text passed from client
        paint_window.type_keys(text)
        time.sleep(0.5)
        
        # Click to exit text mode
        canvas.click_input(coords=(1601, 999))
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added successfully. Proceed with the next step. Do not generate any additional text."
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on primary monitor"""
    global paint_app
    try:
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.2)
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Get primary monitor width
        primary_width = GetSystemMetrics(0)
        
        # First move to primary monitor without specifying size
        ## CHANGED this for my screen
        # win32gui.SetWindowPos(
        #     paint_window.handle,
        #     win32con.HWND_TOP,
        #     primary_width + 1, 0,  # Position it on primary monitor
        #     0, 0,  # Let Windows handle the size
        #     win32con.SWP_NOSIZE  # Don't change the size
        # )
        
        # Now maximize the window
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        time.sleep(0.2)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully on primary monitor and maximized. Proceed with the next step. Do not generate any additional text."
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening Paint: {str(e)}. Retry this step."
                )
            ]
        }
# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    # print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
