#!/usr/bin/env python3
"""
AI Powered - Auto Release Script

This script automates the release process by:
1. Reading current version information from version.yaml
2. Prompting for release type (PATCH, MINOR, MAJOR)
3. Incrementing version information accordingly
4. Generating release notes from git commit history
5. Managing git flow release process
6. Pushing changes to remote repository
"""

import os
import sys
import yaml
import argparse
import subprocess
import re
import tempfile
import logging
import itertools
import threading
import time
from datetime import datetime
from pathlib import Path

MODEL_NAME = "openai/gpt-4.1"  # Alternative: 'mistral-ai/codestral-2501'
RELEASE_AI_PROMPT = """
You are a Release Notes Generator. Your task is to synthesize a list of Git commit messages into clear, concise, 
and user-friendly release notes for a software project.

Input: 
You will be provided with a list of commit messages, typically in a format like:
```<commit_type>(<scope>): <description>```

where <commit_type> follows conventional commits (e.g., feat, fix, chore, docs, style, refactor, perf, test, build, ci).

Output Format: 
Generate release notes with the following sections:
✨ Features: List new features introduced in this release. Use commit messages with feat: type.
🐛 Bug Fixes: List issues that were resolved in this release. Use commit messages with fix: type.
🚀 Improvements: List general enhancements, performance improvements, or refactoring that might be relevant to users.
📚 Documentation: List updates related to documentation. Use commit messages with docs: type.
🧹 Chore & Other: Briefly mention maintenance tasks, build system updates, or other changes that might be noteworthy.

Instructions:
- Process the provided list of commit messages
- Group the commit messages by their type (feat, fix, perf, refactor, docs, chore, etc.)
- For each section, list the descriptions of the relevant commit messages
- Rephrase commit descriptions for clarity and readability in release notes
- If a commit message includes a breaking change, include a separate "🚨 Breaking Changes" section at the top
- Exclude merge commits unless they contain specific, important information
- Order the items within each section logically
- Ensure the tone is professional and informative
"""

# Path to the version.yaml file
YAML_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / 'version.yaml'
PORTAL_TS_VERSION_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / 'portal' / 'src' / 'constants' / 'release.ts'

# Setup logging
def setup_logging():
    """Set up logging for the script."""
    log_dir = os.path.expanduser("~/.autorelease")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logging.basicConfig(
        filename=os.path.join(log_dir, "autorelease.log"),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    return logging.getLogger("autorelease")

# Initialize logger
logger = setup_logging()

def show_spinner(message):
    """Show a spinner while waiting for a process."""
    spinner = itertools.cycle(['-', '/', '|', '\\'])
    stop_spinner = False
    
    def spin():
        sys.stdout.write(message)
        while not stop_spinner:
            sys.stdout.write(next(spinner))
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write('\b')
        sys.stdout.write(' Done!\n')
    
    spinner_thread = threading.Thread(target=spin)
    spinner_thread.start()
    
    def stop():
        nonlocal stop_spinner
        stop_spinner = True
        spinner_thread.join()
    
    return stop

def load_version_data():
    """Load version data from YAML file."""
    try:
        with open(YAML_PATH, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading version data: {e}")
        logger.error(f"Error loading version data: {e}")
        sys.exit(1)

def save_version_data(data):
    """Save version data to YAML file."""
    try:
        with open(YAML_PATH, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)

        with open(PORTAL_TS_VERSION_PATH, 'w') as file:
            file.write(f"export default '{get_new_version_string(data)}';\n")
        return True
    except Exception as e:
        print(f"Error saving version data: {e}")
        logger.error(f"Error saving version data: {e}")
        return False

def get_current_commit_hash():
    """Get the current commit hash."""
    try:
        return run_command("git rev-parse HEAD")
    except Exception as e:
        logger.error(f"Error getting current commit hash: {e}")
        return None

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
        logger.error(f"Command failed: {e.stderr}")
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

def prompt_for_release_type(default='PATCH'):
    """
    Prompt user for release type with a default option.
    
    Args:
        default: Default release type ('PATCH', 'MINOR', or 'MAJOR')
        
    Returns:
        Selected release type
    """
    while True:
        print("\nSelect release type:")
        print(f"1. PATCH - for backwards compatible bug fixes {' (default)' if default == 'PATCH' else ''}")
        print(f"2. MINOR - for new backwards compatible functionality {' (default)' if default == 'MINOR' else ''}")
        print(f"3. MAJOR - for incompatible API changes {' (default)' if default == 'MAJOR' else ''}")
        choice = input(f"Enter choice (1-3 or press Enter for {default}): ")
        
        if choice == '':
            return default
        elif choice == '1':
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

def get_commit_history(version_data):
    """
    Get commit history since the last release using the stored commit ID.
    
    Args:
        version_data: Version data dictionary containing last_commit
        
    Returns:
        List of commit messages
    """
    try:
        # Check if we have a last_commit stored
        last_commit = version_data.get('release', {}).get('last_commit')
        
        if last_commit:
            print(f"Getting commits since last release commit: {last_commit[:7]}")
            logger.info(f"Getting commits since last release commit: {last_commit[:7]}")
            
            # Get commits since the last release commit
            commits = run_command(f"git log {last_commit}..HEAD --pretty=format:'%s'")
            if commits:
                return commits.split('\n')
            else:
                print("No new commits found since last release.")
                logger.info("No new commits found since last release.")
        else:
            # If no last_commit, try using version tag
            current_version = get_new_version_string(version_data)
            tag_check = run_command(f"git tag -l v{current_version}")
            
            if tag_check:
                print(f"Getting commits since tag v{current_version}")
                logger.info(f"Getting commits since tag v{current_version}")
                
                # Get commits since the tag
                commits = run_command(f"git log v{current_version}..HEAD --pretty=format:'%s'")
                if commits:
                    return commits.split('\n')
            
            # If still no commits, get the last 30 commits
            print("No previous release reference found. Getting last 30 commits.")
            logger.info("No previous release reference found. Getting last 30 commits.")
            commits = run_command("git log -30 --pretty=format:'%s'")
            if commits:
                return commits.split('\n')
        
        return []
    except Exception as e:
        print(f"Error getting commit history: {e}")
        logger.error(f"Error getting commit history: {e}")
        return []

def categorize_commits(commits):
    """
    Categorize commits based on conventional commit format.
    
    Args:
        commits: List of commit messages
        
    Returns:
        Dictionary with categorized commits
    """
    categories = {
        'feat': {'title': '🚀 New Features', 'commits': []},
        'fix': {'title': '🐛 Bug Fixes', 'commits': []},
        'docs': {'title': '📚 Documentation', 'commits': []},
        'style': {'title': '💎 Styles', 'commits': []},
        'refactor': {'title': '♻️ Code Refactoring', 'commits': []},
        'perf': {'title': '⚡ Performance Improvements', 'commits': []},
        'test': {'title': '🧪 Tests', 'commits': []},
        'build': {'title': '🔨 Build System', 'commits': []},
        'ci': {'title': '👷 CI/CD', 'commits': []},
        'chore': {'title': '🧹 Chores', 'commits': []},
        'revert': {'title': '⏪ Reverts', 'commits': []},
        'other': {'title': '📦 Other Changes', 'commits': []}
    }
    
    # Regular expression to match conventional commit format
    # Example: feat(component): add new feature
    pattern = r'^(\w+)(?:\(([^\)]+)\))?: (.+)$'
    
    for commit in commits:
        match = re.match(pattern, commit)
        if match:
            type_, scope, message = match.groups()
            if type_ in categories:
                if scope:
                    categories[type_]['commits'].append(f"{message} ({scope})")
                else:
                    categories[type_]['commits'].append(message)
            else:
                categories['other']['commits'].append(commit)
        else:
            categories['other']['commits'].append(commit)
    
    return categories

def generate_release_notes_from_ai(git_commits, new_version):
    """
    Generate release notes using AI model.
    
    Args:
        git_commits: List of commit messages
        new_version: New version string
        
    Returns:
        AI-generated release notes as a string
    """
    logger.info(f"Generating release notes using AI model: {MODEL_NAME}")
    
    # Join commit messages into a single string
    commits_text = "\n".join(git_commits)
    
    # Update prompt with version number
    prompt = RELEASE_AI_PROMPT.replace("[VERSION_NUMBER]", new_version)
    
    try:
        # Prepare prompt with git commits
        full_prompt = f"{prompt}\n\nCommit Messages:\n{commits_text}"[:8000]
        
        # Show spinner while waiting for AI response
        stop_spinner = show_spinner("Generating release notes with AI ")
        
        # Run GitHub CLI models
        result = subprocess.run(['gh', 'models', 'run', MODEL_NAME],
                                input=full_prompt,
                                capture_output=True,
                                text=True,
                                check=True)
        
        # Stop spinner
        stop_spinner()
        
        # Clean up the response
        notes = result.stdout.strip()
        # Remove any markdown code blocks
        notes = re.sub(r'```.*?```', '', notes, flags=re.DOTALL)
        notes = notes.replace('```', '')
        
        return notes
    except subprocess.CalledProcessError as e:
        print(f"Error running AI model: {str(e)}")
        print(f"stderr: {e.stderr}")
        logger.error(f"Error with AI model {MODEL_NAME}: {e.stderr}")
        
        # Fallback to simpler model if available
        if MODEL_NAME != "openai/gpt-3.5-turbo":
            print("Trying fallback model...")
            logger.info("Falling back to gpt-3.5-turbo")
            
            # Change the model and try again
            try:
                result = subprocess.run(['gh', 'models', 'run', "openai/gpt-3.5-turbo"],
                                       input=full_prompt,
                                       capture_output=True,
                                       text=True,
                                       check=True)
                return result.stdout.replace("```", "").strip()
            except Exception as e2:
                print(f"Fallback model also failed: {e2}")
                logger.error(f"Fallback model failed: {e2}")
                return None
        return None
    except FileNotFoundError as e:
        print(f"Error: GitHub CLI not found. Please install it with 'brew install gh' or visit https://cli.github.com/")
        logger.error(f"GitHub CLI not found: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error generating release notes: {e}")
        logger.error(f"Unexpected error generating release notes: {e}")
        return None

def generate_release_notes(version_data, new_version):
    """
    Generate release notes from commit history.
    
    Args:
        version_data: Version data dictionary
        new_version: New version string
        
    Returns:
        Release notes as a string
    """
    print("Generating release notes from commit history...")
    
    # Get commit history
    commits = get_commit_history(version_data)
    
    if not commits:
        print("No commits found for release notes.")
        return None
    
    # Try to generate release notes with AI
    ai_notes = generate_release_notes_from_ai(commits, new_version)
    
    if ai_notes:
        # AI generation successful
        notes = [f"# Release Notes for {new_version}\n"]
        notes.append(f"## Release Date: {datetime.now().strftime('%Y-%m-%d')}\n")
        notes.append(ai_notes)
        notes.append("\n---\n")
        notes.append("*These release notes were automatically generated from commit history.*")
        return "\n".join(notes)
    else:
        # AI generation failed, fall back to categorized commits
        print("AI-generated notes failed. Falling back to categorized commits.")
        logger.warning("AI-generated notes failed. Falling back to categorized commits.")
        
        categorized = categorize_commits(commits)
        
        notes = [f"# Release Notes for {new_version}\n"]
        notes.append(f"## Release Date: {datetime.now().strftime('%Y-%m-%d')}\n")
        
        # Add each category
        for category, data in categorized.items():
            if data['commits']:
                notes.append(f"### {data['title']}\n")
                for commit in data['commits']:
                    notes.append(f"- {commit}")
                notes.append("")  # Empty line between categories
        
        notes.append("\n---\n")
        notes.append("*These release notes were automatically generated from commit history.*")
        
        return "\n".join(notes)

def prompt_to_edit_release_notes(release_notes):
    """
    Prompt user to edit the generated release notes.
    
    Args:
        release_notes: Generated release notes
        
    Returns:
        Final release notes
    """
    print("\nGenerated release notes:")
    print("-" * 50)
    print(release_notes)
    print("-" * 50)
    
    edit = input("\nWould you like to edit these release notes? (y/n): ")
    if edit.lower() == 'y':
        # Create a temporary file with the release notes
        with tempfile.NamedTemporaryFile(suffix=".md", mode='w+', delete=False) as temp:
            temp.write(release_notes)
            temp_filename = temp.name
        
        # Get the default editor
        editor = os.environ.get('EDITOR', 'nano')
        
        # Open the editor with the temporary file
        try:
            subprocess.run([editor, temp_filename], check=True)
            
            # Read the edited notes
            with open(temp_filename, 'r') as temp:
                edited_notes = temp.read()
            
            # Clean up
            os.unlink(temp_filename)
            
            return edited_notes
        except Exception as e:
            print(f"Error editing release notes: {e}")
            logger.error(f"Error editing release notes: {e}")
            # Clean up in case of error
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
            return release_notes
    
    return release_notes

def update_release_status(version_data, default='alpha'):
    """
    Update release status based on user input with a default option.
    
    Args:
        version_data: The version data dictionary
        default: Default release status ('alpha', 'beta', 'rc', or 'final')
        
    Returns:
        Updated version data dictionary
    """
    print("\nSelect release status:")
    print(f"1. alpha - early development version {' (default)' if default == 'alpha' else ''}")
    print(f"2. beta - feature complete but may contain bugs {' (default)' if default == 'beta' else ''}")
    print(f"3. rc - release candidate {' (default)' if default == 'rc' else ''}")
    print(f"4. final - stable release {' (default)' if default == 'final' else ''}")
    
    while True:
        choice = input(f"Enter choice (1-4 or press Enter for {default}): ")
        
        if choice == '':
            version_data['release']['status'] = default
            break
        elif choice == '1':
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
    parser.add_argument("--auto-notes", action="store_true", help="Generate release notes automatically without prompting")
    parser.add_argument("--release-type", choices=["PATCH", "MINOR", "MAJOR"], 
                       help="Specify release type (skips prompt)")
    parser.add_argument("--release-status", choices=["alpha", "beta", "rc", "final"], 
                       help="Specify release status (skips prompt)")
    args = parser.parse_args()
    
    logger.info("Starting auto_release.py")
    
    # Check if git flow is initialized
    check_git_flow()
    
    # Check if repository is clean
    if not args.dry_run:
        check_clean_repo()
    
    # Load current version data
    version_data = load_version_data()
    current_version = get_new_version_string(version_data)
    print(f"Current version: {current_version}")
    logger.info(f"Current version: {current_version}")
    
    # Check for last_commit in version data
    if 'release' not in version_data:
        version_data['release'] = {}
    if 'last_commit' not in version_data['release']:
        version_data['release']['last_commit'] = None
        
    # Show last commit info if available
    if version_data['release']['last_commit']:
        print(f"Last release commit: {version_data['release']['last_commit'][:7]}")
    else:
        print("No previous release commit recorded.")
    
    # Prompt for release type or use command line argument
    if args.release_type:
        release_type = args.release_type
        print(f"Using specified release type: {release_type}")
    else:
        # Always prompt, but use PATCH as default
        release_type = prompt_for_release_type(default='PATCH')
    
    # Increment version
    new_version_data = increment_version(version_data, release_type)
    new_version = get_new_version_string(new_version_data)
    
    # Update release status or use command line argument
    if args.release_status:
        new_version_data['release']['status'] = args.release_status
        print(f"Using specified release status: {args.release_status}")
    else:
        # Always prompt, but use alpha as default
        new_version_data = update_release_status(new_version_data, default='alpha')
    
    print(f"\nNew version will be: {new_version} ({new_version_data['release']['status']})")
    logger.info(f"New version will be: {new_version} ({new_version_data['release']['status']})")
    
    # Generate release notes from commit history
    if release_type != "PATCH":
        auto_release_notes = generate_release_notes(version_data, new_version)
        
        if args.auto_notes:
            release_notes = auto_release_notes
        else:
            # Allow editing of generated release notes
            if auto_release_notes:
                release_notes = prompt_to_edit_release_notes(auto_release_notes)
            else:
                # Fall back to manual entry if no commits found
                print("\nNo commits found for automatic release notes. Please enter them manually.")
                release_notes = prompt_for_release_notes()
    else:
        release_notes = None
    if args.dry_run:
        print("\nDRY RUN - No changes will be made")
        print(f"Would start git flow release: {new_version}")
        print(f"Would update version.yaml to version {new_version}")
        print(f"Would store current commit hash in version.yaml")
        print(f"Would commit with message: Bump version to {new_version}")
        if release_notes:
            print(f"Would create release notes file: release_notes_{new_version}.md")
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
    
    # Get current commit hash before making any changes
    current_commit = get_current_commit_hash()
    if release_type != "PATCH":
        if current_commit:
            # Store the commit hash in version data
            new_version_data['release']['last_commit'] = current_commit
            print(f"Storing current commit hash: {current_commit[:7]}")
            logger.info(f"Storing current commit hash: {current_commit[:7]}")
    
    # Update version.yaml
    print(f"Updating version.yaml to version {new_version}")
    if not save_version_data(new_version_data):
        print("Failed to update version.yaml")
        sys.exit(1)
    
    # Commit changes
    commit_message = f"Bump version to {new_version}"
    print(f"Committing changes: {commit_message}")
    run_command(f"git add .", "Failed to stage version.yaml")
    run_command(f"git commit -m '{commit_message}'", "Failed to commit version change")
    
    # Create release notes file
    if release_notes:
        notes_file = f"release_notes_{new_version}.md"
        print(f"Creating release notes: {notes_file}")
        with open(notes_file, 'w') as f:
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
    logger.info(f"Release {new_version} completed successfully!")

if __name__ == "__main__":
    main()