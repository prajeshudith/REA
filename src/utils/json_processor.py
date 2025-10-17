import json
import re

def extract_json_from_markdown(text):
    """
    Extract JSON from markdown code blocks and return as a Python dictionary.
    
    Args:
        text (str): Input text containing JSON in markdown code blocks
        
    Returns:
        dict: Parsed JSON as a Python dictionary
        
    Raises:
        ValueError: If no JSON found or JSON is invalid
    """
    # Pattern to match ```json ... ``` or ``` ... ```
    pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    
    # Search for the pattern (DOTALL flag allows matching across newlines)
    match = re.search(pattern, text, re.DOTALL)
    
    if not match:
        raise ValueError("No JSON code block found in the text")
    
    # Extract the JSON string
    json_str = match.group(1)
    
    # Parse and return the JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")