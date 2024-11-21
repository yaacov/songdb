import os
import glob
import shutil


def clean_up():
    # Remove compiled Python files
    pyc_files = glob.glob("**/*.pyc", recursive=True)
    pycache_dirs = glob.glob("**/__pycache__", recursive=True)
    for file in pyc_files:
        print(f"Removing {file}...")
        os.remove(file)
    for directory in pycache_dirs:
        print(f"Removing directory {directory}...")
        shutil.rmtree(directory)

    # Remove SQLite databases
    if os.path.exists("songs.db"):
        print("Removing songs.db...")
        os.remove("songs.db")

    # Remove other artifacts (e.g., logs, temporary files, etc.)
    pem_files = glob.glob("**/*.pem", recursive=True)
    for file in pem_files:
        print(f"Removing {file}...")
        os.remove(file)

    # Remove pytest cache
    pytest_cache_dirs = glob.glob(".pytest_cache", recursive=True)
    for directory in pytest_cache_dirs:
        print(f"Removing pytest cache directory {directory}...")
        shutil.rmtree(directory)


if __name__ == "__main__":
    clean_up()
