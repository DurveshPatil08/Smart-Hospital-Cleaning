import os

def generate_project_summary(root_dir, output_file):
    """
    Generates a text file containing the project's directory structure
    and the contents of all non-excluded files.

    Args:
        root_dir (str): The path to the root directory of the project.
        output_file (str): The name of the file to save the summary to.
    """
    # --- Configuration for Exclusions ---
    # Add any folders, files, or extensions you want to ignore here.
    excluded_dirs = {
        '__pycache__',
        '.git',
        '.idea',
        'venv',
        '.vscode',
        # Add any other virtual environment folders if needed
        # e.g., 'env', '.venv'
    }
    excluded_files = {
        '.env',
        output_file, # Exclude the script's own output file
        'create_summary.py', # Exclude the script itself
    }
    excluded_extensions = {
        '.pyc',
        '.pyo',
        '.pyd',
        '.log',
        # Image and binary files
        '.jpg',
        '.jpeg',
        '.png',
        '.gif',
        '.svg',
        '.ico',
        '.bmp',
        '.tif',
        '.tiff',
        '.webp',
        '.DS_Store',
    }

    # --- 1. Generate the Directory Tree ---
    project_structure = "Project Structure:\n"
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter out excluded directories from further traversal
        dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
        
        # Calculate indentation level
        level = dirpath.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        
        # Add the current directory to the structure string
        if level > 0: # Avoid printing the root dir name twice
            project_structure += f"{indent[:-4]}└── {os.path.basename(dirpath)}/\n"
        
        # Add files in the current directory to the structure string
        sub_indent = indent + '    '
        for f in filenames:
            if f not in excluded_files and not any(f.endswith(ext) for ext in excluded_extensions):
                project_structure += f"{sub_indent}├── {f}\n"

    # --- 2. Get all valid file paths ---
    all_files_content = ""
    filepaths_to_include = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude specified directories from the walk
        dirnames[:] = [d for d in dirnames if d not in excluded_dirs]

        for filename in filenames:
            # Check against excluded files and extensions
            if filename in excluded_files or any(filename.endswith(ext) for ext in excluded_extensions):
                continue

            filepaths_to_include.append(os.path.join(dirpath, filename))

    # --- 3. Read the content of each valid file ---
    filepaths_to_include.sort() # Sort for consistent order
    for filepath in filepaths_to_include:
        relative_path = os.path.relpath(filepath, root_dir)
        separator = f"\n{'='*20} FILE: {relative_path} {'='*20}\n\n"
        all_files_content += separator
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                all_files_content += file.read()
        except Exception as e:
            all_files_content += f"Could not read file. Error: {e}\n"

    # --- 4. Write everything to the output file ---
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(project_structure)
            f.write("\n\n" + "="*80 + "\n\n")
            f.write("File Contents:\n")
            f.write(all_files_content)
        print(f"✅ Project summary successfully generated in '{output_file}'")
    except Exception as e:
        print(f"❌ An error occurred while writing to the file: {e}")

if __name__ == "__main__":
    # The script will run from the directory it's in.
    # This assumes you place it in the root of your project.
    current_directory = os.getcwd() 
    output_filename = "project_summary.txt"
    generate_project_summary(current_directory, output_filename)