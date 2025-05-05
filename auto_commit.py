#!/usr/bin/env python3
import subprocess
MODEL_NAME = "openai/gpt-4.1" #'mistral-ai/codestral-2501'
COMMIT_MESSAGE_PROMPT = """
Write a meaningful commit message in the conventional commit convention by trying to understand 
what was the benefits the code author wanted to add by his changes to codebase with this commit. 
I'll send you an output of 'git diff --staged' command, and you convert it into a commit message. 

Requirements:
- Lines must not be longer than 74 characters. 
- Use EN language to answer. 
- End commit title with issue number if you can get it from the branch name: {branch} in parenthesis. 
- Try to use line breaks, only after a dot, to help making the commit message easier to read..
- Use bullet points to list the changes (do not mention filename extensions).
- Follow the bullet points with a single sentence explaining the necessity of these changes.
- Be brief and concise throughout.
- Output only the commit message."""

def get_git_diff():
    try:
        subprocess.run(['git', 'add', '.'],
                       capture_output=True,
                       text=True,
                       check=True)

        result = subprocess.run(['git', 'diff', '--minimal'],
                                capture_output=True,
                                text=True,
                                check=True)
        result2 = subprocess.run(['git', 'diff', '--staged', '--minimal'],
                                 capture_output=True,
                                 text=True,
                                 check=True)
        return f"{result.stdout}\n{result2.stdout}"
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {str(e)}")
        return None


def get_commit_message(system_prompt, git_diff_output):
    try:
        # First, read the file
        prompt = f'{system_prompt}"""{git_diff_output}"""'[:8000]
        # Then run gh models
        result = subprocess.run(['gh', 'models', 'run', MODEL_NAME],
                                input=prompt,
                                capture_output=True,
                                text=True,
                                check=True)

        return result.stdout.replace("```", "").strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running gh models: {str(e)}")
        print(f"stderr: {e.stderr}")
        return None
    except FileNotFoundError as e:
        print(f"Error reading file: {str(e)}")
        return None


def get_user_confirmation_for_commit(commit_message):
    print(f"\nProposed commit message:\n{'-' * 50}\n{commit_message}\n{'-' * 50}")
    while True:
        response = input("\nDo you want to proceed with this commit? (y/n): ").lower().strip()
        if response in ['y', 'n']:
            return response == 'y'
        print("Please enter 'y' for yes or 'n' for no.")

def get_user_confirmation_for_push():
    while True:
        response = input("\nDo you want to push commit(s) to remote? (y/n): ").lower().strip()
        if response in ['y', 'n']:
            return response == 'y'
        print("Please enter 'y' for yes or 'n' for no.")

def main():
    git_diff_output = get_git_diff()
    if git_diff_output:

        try:
            # Your existing code to generate commit message
            commit_message = get_commit_message(system_prompt=COMMIT_MESSAGE_PROMPT, git_diff_output=git_diff_output)

            if not commit_message:
                print("Failed to generate commit message. Aborting.")
                print("-" * 80)
                print(git_diff_output)
                return
            # Ask for user confirmation
            if get_user_confirmation_for_commit(commit_message):
                # Proceed with git commit
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                print("Changes committed successfully!")
                if get_user_confirmation_for_push():
                    subprocess.run(['git', 'push'], check=True)
                    print("Changes pushed successfully!")
                else:
                    print("Git push cancelled by user.")
            else:
                print("Commit cancelled by user.")

        except subprocess.CalledProcessError as e:
            print(f"Error during git operations: {e}")
            print(f"Error output: {e.stderr}")


    else:
        print("No git diff found.")


if __name__ == '__main__':
    main()
