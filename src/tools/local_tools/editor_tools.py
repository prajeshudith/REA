import os
from typing import Optional
from langchain.tools import StructuredTool

# ------------------------------- Helper Functions -------------------------------
def write_file(path: str, content: str) -> str:
    """Writes or creates a file in the local system."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"✅ File written successfully to {path}"


def read_file(path: str) -> str:
    """Reads a file from the local system."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"❌ File not found: {path}"
    except Exception as e:
        return f"❌ Error reading file {path}: {str(e)}"
    

def list_files_in_root(folders_to_omit: list) -> str:
    """Lists all files in the root directory and with all the files inside the subdirectories with their paths.
    Should not include the files in given folders_to_omit.
    All the paths should have '/' for directory separator."""
    file_list = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if not any(folder in root for folder in folders_to_omit):
                file_list.append(os.path.relpath(os.path.join(root, file), ".").replace("\\", "/"))
    return "\n".join(file_list)


#------------------------------- Tools -------------------------------
def get_writer_tool():
    writer_tool = StructuredTool.from_function(
        func=write_file,
        name="write_create_file",
        description=(
            "Writes or creates a file in the local system. "
            "Args: path (str): file path to save to; "
            "content (str): content to write to the file."
        ),
    )
    return writer_tool

    
def get_reader_tool():
    reader_tool = StructuredTool.from_function(
        func=read_file,
        name="read_file",
        description=(
            "Reads a file from the local system. "
            "Args: path (str): file path to read from."
        ),
    )
    return reader_tool

def get_file_lister_tool(folders_to_omit: Optional[list] = None):
    if folders_to_omit is None:
        folders_to_omit = ["node_modules", ".git", "__pycache__", "venv", ".venv", "env", ".env","dump"]
    lister_tool = StructuredTool.from_function(
        func=lambda: list_files_in_root(folders_to_omit),
        name="list_files",
        description=(
            "Lists all files in the root directory and with all the files inside the subdirectories with their paths. "
            "Should not include the files in given folders_to_omit. "
            "All the paths should have '/' for directory separator. "
            "Args: None"
        ),
    )
    return lister_tool