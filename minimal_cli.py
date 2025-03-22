#!/usr/bin/env python3
"""
Ultra-minimal CLI interface for Jarvis that bypasses most components.
"""
import os
import sys
import readline  # for command history
import json
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Import minimal required components
from jarvis.config.settings_manager import settings_manager
import jarvis.config.settings as settings

# Create direct OpenAI API helper
def get_openai_response(query):
    """Get a response directly from OpenAI API."""
    try:
        import openai
        
        # Get OpenAI API key from settings or .env
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
            
        if not api_key:
            return "Error: No OpenAI API key found in settings or environment variables."
            
        # Set the API key
        openai.api_key = api_key
        
        # Make the API call
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Jarvis, a helpful AI assistant."},
                {"role": "user", "content": query}
            ]
        )
        
        # Extract and return the response text
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def save_to_history(query, response):
    """Save the interaction to a simple history file."""
    history_dir = Path(os.path.expanduser("~/.jarvis/history"))
    history_dir.mkdir(exist_ok=True, parents=True)
    
    history_file = history_dir / "cli_history.jsonl"
    
    with open(history_file, "a") as f:
        entry = {
            "query": query,
            "response": response,
            "timestamp": str(Path.ctime(Path()))
        }
        f.write(json.dumps(entry) + "\n")

def main():
    """Minimal CLI interface for Jarvis."""
    print("Welcome to Jarvis Ultra-Minimal CLI!")
    print("This version bypasses most components and uses OpenAI API directly.")
    print("Type 'exit' or 'quit' to end the session.")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ")
            
            # Check for exit command
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nJarvis: Goodbye!")
                break
                
            # Get and print the response
            response = get_openai_response(user_input)
            print(f"\nJarvis: {response}")
            
            # Save to history
            save_to_history(user_input, response)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            
if __name__ == "__main__":
    main() 