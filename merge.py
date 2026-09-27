#!/usr/bin/env python3
import os
from pathlib import Path

def merge_code_to_markdown(source_dir, output_file, allowed_extensions=None, ignore_dirs=None):
    """
    Merges all source code files from a directory into a single Markdown file.
    """
    source_path = Path(source_dir)
    output_path = Path(output_file)
    
    # Default extensions to search for if none provided
    if allowed_extensions is None:
        allowed_extensions = {'.py', '.tcl', '.css', '.js', '.json', '.md', '.txt', '.c', '.h', '.go', '.hpp', '.cpp', '.mm'}
        
    # Folders to completely skip (standard ignores for development)
    if ignore_dirs is None:
        ignore_dirs = {'__pycache__', '.git', '.venv', 'venv', 'env', 'node_modules', '.idea', '.vscode', 'build', 'dist', 'prismtk', 'ctk'}

    # Mapping file extensions to markdown language identifiers for syntax highlighting
    lang_mapping = {
        '.py': 'python',
        '.tcl': 'tcl',
        '.css': 'css',
        '.js': 'javascript',
        '.json': 'json',
        '.md': 'markdown',
        '.c': 'c',
        '.h': 'c',
        '.go': 'go',
        '.txt': 'text',
        '.hpp': 'cpp',
        '.cpp': 'cpp',
        '.mm': 'cpp'
    }

    print(f"🔍 Scanning '{source_path.resolve()}' for code files...")
    
    merged_count = 0

    with open(output_path, 'w', encoding='utf-8') as md_file:
        # Write a title/header for the markdown file
        md_file.write(f"# Project Source Code Archive\n")
        md_file.write(f"Generated automatically from directory: `{source_path.name}`\n\n")
        md_file.write("---\n\n")

        # Walk through directories
        for root, dirs, files in os.walk(source_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                if ext in allowed_extensions:
                    # Calculate relative path to show cleanly in the Markdown header
                    rel_path = file_path.relative_to(source_path)
                    lang = lang_mapping.get(ext, '')
                    
                    print(f"📄 Adding: {rel_path}")
                    
                    # Write the markdown section header for this file
                    md_file.write(f"## File: `{rel_path}`\n\n")
                    md_file.write(f"```{lang}\n")
                    
                    # Read and append file contents safely
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as code_file:
                            md_file.write(code_file.read())
                    except Exception as e:
                        md_file.write(f"// Error reading file: {str(e)}\n")
                    
                    # Close code block and add spacing
                    md_file.write("\n```\n\n")
                    md_file.write("---\n\n")
                    merged_count += 1

    print(f"✨ Success! Merged {merged_count} files into '{output_path.resolve()}'")

# --- Example Usage ---
if __name__ == "__main__":
    # Target directory ('.' means current directory where script runs)
    SOURCE_DIRECTORY = "./src/" 
    
    # Name of the output markdown file
    OUTPUT_MARKDOWN = "tkblend.md"
    
    # Run the script
    merge_code_to_markdown(SOURCE_DIRECTORY, OUTPUT_MARKDOWN)

    # Target directory ('.' means current directory where script runs)
    SOURCE_DIRECTORY = "./tkblend/" 
    
    # Name of the output markdown file
    OUTPUT_MARKDOWN = "tkblend_python.md"
    
    # Run the script
    merge_code_to_markdown(SOURCE_DIRECTORY, OUTPUT_MARKDOWN)
