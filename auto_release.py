#!/usr/bin/env python3
"""
Jubilee eKYC Auto Release Script

This script automates the release process by:
1. Reading current version information from version.yaml
2. Prompting for release type (PATCH, MINOR, MAJOR)
3. Incrementing version information accordingly
4. Managing git flow release process
5. Pushing changes to remote repository
"""

import os
import sys
import yaml
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Path to the version.yaml file
YAML_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / 'version.yaml'

def load_version_data():
    """Load version data from YAML file."""
    try:
        with open(YAML_PATH, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading version data: {e}")
        sys.exit(1)

def save_version_data(data):
    """Save version data to YAML file."""
    try:
        with open(YAML_PATH, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error saving version data: {e}")
        return False

def increment_version(version_data, release_type):
    """
    Increment version based on release type.
    
    Args:
        version_data: The current version data dictionary
        release_type: One of 'PATCH', 'MINOR', or 'MAJOR'
    
    Returns:
        Updated version data dictionary
    """
    if release_type == 'PATCH':
        version_data['version']['patch'] += 1
    elif release_type == 'MINOR':
        version_data['version']['minor'] += 1
        version_data['version']['patch'] = 0
    elif release_type == 'MAJOR':
        version_data['version']['major'] += 1
        version_data['version']['minor'] = 0
        version_data['version']['patch'] = 0
    
    # Update release date to today
    version_data['release']['date'] = datetime.now().strftime('%Y-%m-%d')
    
    return version_data

def get_new_version_string(version_data):
    """Generate version string from version data."""
    major = version_data['version']['major']
    minor = version_data['version']['minor']
    patch = version_data['version']['patch']
    return f"{major}.{minor}.{patch}"

def run_command(command, error_message=None):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if error_message:
            print(f"{error_message}: {e}")
        else:
            print(f"Command failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def check_git_flow():
    """Check if git flow is initialized."""
    result = run_command("git flow config", "Failed to check git flow configuration")
    if not result:
        print("Git flow doesn't appear to be initialized.")
        init = input("Would you like to initialize git flow with default settings? (y/n): ")
        if init.lower() == 'y':
            run_command("git flow init -d", "Failed to initialize git flow")
        else:
            print("Please initialize git flow manually and try again.")
            sys.exit(1)

def check_clean_repo():
    """Check if the repository is clean (no uncommitted changes)."""
    status = run_command("git status --porcelain")
    if status:
        print("Error: Repository has uncommitted changes.")
        print("Please commit or stash your changes before running this script.")
        sys.exit(1)

def prompt_for_release_type():
    """Prompt user for release type."""
    while True:
        print("\nSelect release type:")
        print("1. PATCH - for backwards compatible bug fixes")
        print("2. MINOR - for new backwards compatible functionality")
        print("3. MAJOR - for incompatible API changes")
        choice = input("Enter choice (1-3): ")
        
        if choice == '1':
            return 'PATCH'
        elif choice == '2':
            return 'MINOR'
        elif choice == '3':
            return 'MAJOR'
        else:
            print("Invalid choice. Please try again.")

def prompt_for_release_notes():
    """Prompt user for release notes."""
    print("\nEnter release notes (end with a line containing only '---'):")
    lines = []
    while True:
        line = input()
        if line == '---':
            break
        lines.append(line)
    return '\n'.join(lines)

def update_release_status(version_data):
    """Update release status based on user input."""
    print("\nSelect release status:")
    print("1. alpha - early development version")
    print("2. beta - feature complete but may contain bugs")
    print("3. rc - release candidate")
    print("4. final - stable release")
    
    while True:
        choice = input("Enter choice (1-4): ")
        if choice == '1':
            version_data['release']['status'] = 'alpha'
            break
        elif choice == '2':
            version_data['release']['status'] = 'beta'
            break
        elif choice == '3':
            version_data['release']['status'] = 'rc'
            break
        elif choice == '4':
            version_data['release']['status'] = 'final'
            break
        else:
            print("Invalid choice. Please try again.")
    
    return version_data

def main():
    parser = argparse.ArgumentParser(description="Automate the release process for Jubilee eKYC")
    parser.add_argument("--no-push", action="store_true", help="Don't push to remote repository")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")
    args = parser.parse_args()
    
    # Check if git flow is initialized
    check_git_flow()
    
    # Check if repository is clean
    if not args.dry_run:
        check_clean_repo()
    
    # Load current version data
    version_data = load_version_data()
    current_version = get_new_version_string(version_data)
    print(f"Current version: {current_version}")
    
    # Prompt for release type
    release_type = prompt_for_release_type()
    
    # Increment version
    new_version_data = increment_version(version_data, release_type)
    new_version = get_new_version_string(new_version_data)
    
    # Update release status
    new_version_data = update_release_status(new_version_data)
    
    print(f"\nNew version will be: {new_version} ({new_version_data['release']['status']})")
    
    # Prompt for release notes
    release_notes = prompt_for_release_notes()
    
    if args.dry_run:
        print("\nDRY RUN - No changes will be made")
        print(f"Would start git flow release: {new_version}")
        print(f"Would update version.yaml to version {new_version}")
        print(f"Would commit with message: Bump version to {new_version}")
        print(f"Would finish git flow release: {new_version}")
        if not args.no_push:
            print("Would push develop and main branches to origin")
        return
    
    # Start git flow release
    print(f"\nStarting git flow release: {new_version}")
    result = run_command(f"git flow release start {new_version}", 
                        f"Failed to start git flow release {new_version}")
    if not result:
        sys.exit(1)
    
    # Update version.yaml
    print(f"Updating version.yaml to version {new_version}")
    if not save_version_data(new_version_data):
        print("Failed to update version.yaml")
        sys.exit(1)
    
    # Commit changes
    commit_message = f"Bump version to {new_version}"
    print(f"Committing changes: {commit_message}")
    run_command(f"git add {YAML_PATH}", "Failed to stage version.yaml")
    run_command(f"git commit -m '{commit_message}'", "Failed to commit version change")
    
    # Create release notes file
    if release_notes:
        notes_file = f"release_notes_{new_version}.md"
        print(f"Creating release notes: {notes_file}")
        with open(notes_file, 'w') as f:
            f.write(f"# Release Notes for {new_version}\n\n")
            f.write(release_notes)
        run_command(f"git add {notes_file}", "Failed to stage release notes")
        run_command(f"git commit -m 'Add release notes for {new_version}'", 
                   "Failed to commit release notes")
    
    # Finish git flow release
    print(f"Finishing git flow release: {new_version}")
    run_command(f"git flow release finish -m 'Release {new_version}' {new_version}", 
               f"Failed to finish git flow release {new_version}")
    
    # Push to remote if requested
    if not args.no_push:
        push = input("\nPush changes to remote repository? (y/n): ")
        if push.lower() == 'y':
            print("Pushing develop and main branches to origin")
            run_command("git push origin develop", "Failed to push develop branch")
            run_command("git push origin main", "Failed to push main branch")
            run_command("git push --tags", "Failed to push tags")
            print("Successfully pushed changes to remote repository")
    
    print(f"\nRelease {new_version} completed successfully!")

if __name__ == "__main__":
    main()