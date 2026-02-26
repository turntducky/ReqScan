import ast
import os
import sys
import sysconfig
import importlib.metadata
import importlib.util
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

# Enable ANSI colors on Windows
if os.name == 'nt':
    os.system("")

# -------- COLORS --------
class C:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# -------- CONFIG --------
SKIP_DIRS = {
    ".git", "venv", ".venv", "env", ".env", "envs", "node_modules", 
    "__pycache__", "build", "dist", ".idea", ".vscode", "site-packages"
}
# ------------------------

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""{C.CYAN}{C.BOLD}
  _____             _____                  
 |  __ \           / ____|                 
 | |__) |___  __ _| (___   ___ __ _ _ __   
 |  _  // _ \/ _` |\___ \ / __/ _` | '_ \  
 | | \ \  __/ (_| |____) | (_| (_| | | | | 
 |_|  \_\___|\__, |_____/ \___\__,_|_| |_| 
                | |                        
                |_|  
                      
 | Developed by : turnt ducky 🦆 | {C.RESET}
    """
    print(banner)

# ---------------- ENVIRONMENT DETECTION ----------------
def is_venv(dir_path):
    path = Path(dir_path)
    return (
        (path / "pyvenv.cfg").exists() or 
        (path / "bin" / "python").exists() or 
        (path / "Scripts" / "python.exe").exists()
    )

# ---------------- FILE DISCOVERY ----------------
def get_python_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames 
            if d not in SKIP_DIRS and not is_venv(os.path.join(dirpath, d))
        ]
        for file in filenames:
            if file.endswith(".py"):
                yield os.path.join(dirpath, file)

# ---------------- IMPORT EXTRACTION ----------------
def extract_imports(file_path):
    imports = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError, IOError):
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.add(name.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                imports.add(node.module.split(".")[0])
    return imports

# ---------------- MODULE CLASSIFICATION ----------------
def get_stdlib_modules():
    stdlib = set(sys.stdlib_module_names)
    stdlib_path = Path(sysconfig.get_paths()["stdlib"])
    for p in stdlib_path.glob("*.py"):
        stdlib.add(p.stem)
    return stdlib

def is_local_import(name, project_root):
    try:
        spec = importlib.util.find_spec(name)
        if spec and spec.origin and spec.origin not in ('built-in', 'frozen'):
            return Path(spec.origin).resolve().is_relative_to(project_root.resolve())
    except Exception:
        pass
    return False

def get_local_modules(project_root):
    local = set()
    local.add(Path(project_root).name)
    for dirpath, dirnames, filenames in os.walk(project_root):
        dirnames[:] = [
            d for d in dirnames 
            if d not in SKIP_DIRS and not is_venv(os.path.join(dirpath, d))
        ]
        for d in dirnames:
            local.add(d)
        for f in filenames:
            if f.endswith(".py"):
                local.add(os.path.splitext(f)[0])
    return local

def get_package_map():
    mapping = {}
    for dist in importlib.metadata.distributions():
        package_name = dist.metadata.get("Name")
        if not package_name:
            continue
        try:
            top_level = dist.read_text("top_level.txt")
            if top_level:
                for line in top_level.splitlines():
                    name = line.strip()
                    if name:
                        mapping.setdefault(name, package_name)
            else:
                normalized = package_name.lower().replace("-", "_")
                mapping.setdefault(normalized, package_name)
                mapping.setdefault(package_name.lower(), package_name)
        except Exception:
            continue
    return mapping

# ---------------- MAIN ----------------
def main():
    clear_screen()
    print_banner()
    
    # 1. Path Selection
    print(f" {C.CYAN}[*]{C.RESET} Choose project location:")
    print(f"     {C.BOLD}1.{C.RESET} Current directory ({C.YELLOW}{Path.cwd()}{C.RESET})")
    print(f"     {C.BOLD}2.{C.RESET} Enter a custom path")
    path_choice = input(f"     Select (1 or 2) [1]: ").strip()

    if path_choice == "2":
        raw_input = input(f"\n {C.CYAN}[*]{C.RESET} Enter project folder path: ").strip()
        project_root = Path(raw_input.replace('"', '').replace("'", ""))
    else:
        project_root = Path.cwd()

    if not project_root.exists() or not project_root.is_dir():
        print(f"\n {C.RED}[!]{C.RESET} Error: Directory does not exist: {project_root}")
        return

    # 2. Output Destination
    print(f"\n {C.CYAN}[*]{C.RESET} Where should requirements.txt be saved?")
    print(f"     {C.BOLD}1.{C.RESET} Inside the scanned project directory")
    print(f"     {C.BOLD}2.{C.RESET} In the current directory (here)")
    choice = input(f"     Select (1 or 2) [1]: ").strip()
    
    output_file = Path.cwd() / "requirements.txt" if choice == "2" else project_root / "requirements.txt"

    print(f"\n {C.CYAN}[*]{C.RESET} Scanning project: {C.YELLOW}{project_root}{C.RESET}")
    
    py_files = list(get_python_files(project_root))
    print(f" {C.GREEN}[+]{C.RESET} Found {len(py_files)} Python files.")

    if not py_files:
        print(f" {C.RED}[!]{C.RESET} No files to process. Check your path or SKIP_DIRS.")
        return

    # 3. Parse and Resolve
    all_imports = set()
    print(f" {C.CYAN}[*]{C.RESET} Parsing imports in parallel...")
    
    with ProcessPoolExecutor() as executor:
        results = executor.map(extract_imports, py_files)
        for file_imports in results:
            all_imports.update(file_imports)

    stdlib = get_stdlib_modules()
    local_modules = get_local_modules(project_root)
    pkg_map = get_package_map()

    external_imports = {
        imp for imp in all_imports 
        if imp not in stdlib 
        and imp not in local_modules 
        and not is_local_import(imp, project_root)
    }

    final_requirements = {}
    for imp in external_imports:
        actual_package = pkg_map.get(imp, imp)
        try:
            raw_version = importlib.metadata.version(actual_package)
            clean_version = raw_version.split("+")[0]
            final_requirements[actual_package] = clean_version
        except importlib.metadata.PackageNotFoundError:
            continue

    if not final_requirements:
        print(f"\n {C.CYAN}─────────────────────────────────────────{C.RESET}")
        print(f" {C.YELLOW}[i]{C.RESET} No external dependencies detected.")
        print(f" {C.GREEN}[✓]{C.RESET} Your project only uses the Standard Library (or local modules)!")
        print(f" {C.CYAN}─────────────────────────────────────────{C.RESET}\n")
        return

    # 4. Handle Existing requirements.txt
    merged_requirements = {}
    if output_file.exists():
        print(f"\n {C.YELLOW}[i]{C.RESET} Found existing {C.BOLD}requirements.txt{C.RESET} at the destination.")
        print(f"     {C.BOLD}1.{C.RESET} Merge (Keep manual additions, update detected versions)")
        print(f"     {C.BOLD}2.{C.RESET} Overwrite (Create a fresh file)")
        merge_choice = input(f"     Select (1 or 2) [1]: ").strip()
        
        if merge_choice != "2":
            # Parse existing file
            with open(output_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Handle formats like pkg==1.0.0 or pkg>=1.0.0
                    if "==" in line:
                        pkg, ver = line.split("==", 1)
                        merged_requirements[pkg.strip()] = ver.strip()
                    elif ">=" in line:
                        pkg, ver = line.split(">=", 1)
                        # Store the operator with the version so it writes out correctly
                        merged_requirements[pkg.strip()] = f">={ver.strip()}"
                    else:
                        merged_requirements[line] = None

    # Merge newly detected requirements (overwrites old versions with detected ones)
    for pkg, version in final_requirements.items():
        # Only prefix with == if it's a clean version string and not already formatted from an old file
        if version and not str(version).startswith((">=", "<=", "==")):
            merged_requirements[pkg] = f"=={version}"
        elif version:
            merged_requirements[pkg] = version
        else:
            if pkg not in merged_requirements:
                merged_requirements[pkg] = None

    # 5. Output
    with open(output_file, "w", encoding="utf-8") as f:
        for pkg, version in sorted(merged_requirements.items(), key=lambda x: x[0].lower()):
            if version:
                # If version already includes an operator (from a merge), use it directly
                if version.startswith((">=", "<=", "==")):
                    f.write(f"{pkg}{version}\n")
                else:
                    f.write(f"{pkg}=={version}\n")
            else:
                f.write(f"{pkg}\n")

    print(f"\n {C.CYAN}─────────────────────────────────────────{C.RESET}")
    print(f" {C.GREEN}[✓]{C.RESET} Final package count: {C.BOLD}{len(merged_requirements)}{C.RESET}")
    print(f" {C.GREEN}[✓]{C.RESET} Successfully generated:\n     {C.YELLOW}{output_file}{C.RESET}")
    print(f" {C.CYAN}─────────────────────────────────────────{C.RESET}\n")

if __name__ == "__main__":
    main()
