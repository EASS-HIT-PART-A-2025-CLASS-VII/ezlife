import os
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import logging

from breakdown_utils import generate_simple_breakdown  # Import the new utility

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file in parent backend directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
print(f"Loading .env from: {dotenv_path}")
print(f"Path exists: {os.path.exists(dotenv_path)}")
load_dotenv(dotenv_path=dotenv_path)

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

print(f"OPENROUTER_API_KEY loaded: {'Yes' if OPENROUTER_API_KEY else 'No'}")
if OPENROUTER_API_KEY:
    print(f"API Key starts with: {OPENROUTER_API_KEY[:10]}...")

if not OPENROUTER_API_KEY:
    logging.warning("OPENROUTER_API_KEY not found in environment variables. AI estimator will likely fail.")

# Available models to try in order (fallback mechanism)
AVAILABLE_MODELS = [
    "microsoft/wizardlm-2-8x22b",      # First choice - Free and powerful
    "meta-llama/llama-3.1-8b-instruct", # Second choice - Llama 3.1
    "mistralai/mistral-7b-instruct",   # Third choice - Mistral 7B Instruct
    "google/gemma-2-9b-it",            # Fourth choice - Gemma 2
    "anthropic/claude-3-haiku"         # Last resort - Claude (uses credits)
]

# Headers required for OpenRouter API
headers = {
    "Content-Type": "application/json",
    "HTTP-Referer": "https://ezlife-taskmanager.com",  # Required for OpenRouter
    "X-Title": "EZLife Task Manager"   # App name
}
if OPENROUTER_API_KEY:
    headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY}"

def get_time_estimate(description: str, model: str) -> int:
    """
    Helper function to get time estimate from a specific model
    """
    # Enhanced system prompt for beginner-level estimation with overhead
    system_prompt = """You are an expert task time estimation assistant specialized in estimating realistic time requirements for BEGINNERS.

    ESTIMATION PRINCIPLES:
    1. Always estimate for someone who is a BEGINNER at the task
    2. Include realistic overhead for learning, mistakes, and iterations
    3. Account for the extra time beginners need compared to experts
    4. Consider real-world challenges and setbacks

    OVERHEAD CALCULATION GUIDELINES:
    - For learning tasks: Add 30-50% overhead for trial and error
    - For technical tasks: Add 40-60% overhead for debugging and troubleshooting
    - For creative tasks: Add 25-40% overhead for iterations and refinements
    - For complex multi-step tasks: Add 50-70% overhead for coordination and planning
    - For completely new skills: Add 60-80% overhead for foundational learning

    BEGINNER FACTORS TO CONSIDER:
    - Time to understand concepts and terminology
    - Research time to find resources and tutorials
    - Setup and configuration difficulties
    - Common beginner mistakes and debugging time
    - Multiple attempts to get things working
    - Time to ask for help and find solutions
    - Practice time to build confidence
    - Documentation reading and understanding

    REALISTIC TIME EXAMPLES:
    - "learn basic HTML" → 720 minutes (12 hours with beginner overhead)
    - "learn Python programming basics" → 4800 minutes (80 hours for true beginner)
    - "build first simple website" → 2400 minutes (40 hours including learning and debugging)
    - "write first business plan" → 1800 minutes (30 hours with research and revisions)
    - "learn to use Excel" → 960 minutes (16 hours with practice and mistakes)

    IMPORTANT: Respond with ONLY a number representing minutes. No text, no explanations, just the number.
    Be generous with time estimates - it's better to overestimate than leave someone frustrated.
    """
    
    # User prompt with task description and beginner context
    user_prompt = f"""Task: {description}

Please estimate how many minutes this task would take for a COMPLETE BEGINNER, including:
- Learning time for any required skills
- Time for mistakes, troubleshooting, and iterations
- Appropriate overhead for inexperience
- Setup and preparation time

Provide only the number of minutes."""
    
    # Prepare payload for OpenRouter API (following OpenAI format)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,  # Slightly higher for more realistic variation
        "max_tokens": 100    # Increased to allow for longer responses and reasoning
    }
    
    logging.info(f"Requesting estimation from model: {model} for task: '{description[:50]}...'")
    
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=15) 
        
        if response.status_code == 200:
            result = response.json()
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logging.info(f"Raw response from {model}: {text}")
            
            # Extract numbers from the response
            digits = ''.join(filter(str.isdigit, text))
            if digits:
                minutes = int(digits)
                # Sanity check - if estimate is absurdly high, cap it (for beginners, allow up to 2 weeks)
                if minutes > 1440 * 14:  # More than 2 weeks in minutes (20,160 minutes)
                    logging.warning(f"Extremely high estimate ({minutes} min) from {model} capped to reasonable maximum.")
                    minutes = 1440 * 7  # Cap at 1 week (10,080 minutes)
                return minutes
            else:
                logging.warning(f"No digits found in response from {model}: '{text}'")
                return None
        else:
            logging.error(f"API request to {model} failed with status {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logging.error(f"Timeout during API request to {model}.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception during API call to {model}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_time_estimate with {model}: {str(e)}")
        return None


def get_task_breakdown(description: str, total_minutes: int, days_per_week: int, hours_per_day: float, model: str = "mistralai/mistral-7b-instruct") -> List[Dict]:
    """
    Generate a breakdown of a task into daily chunks with summaries using an AI model.
    If AI fails, it falls back to `generate_simple_breakdown`.
    """
    logging.info(f"Generating AI task breakdown for: '{description[:50]}...' ({total_minutes} min)")
    
    if not all([isinstance(days_per_week, (int, float)), days_per_week > 0,
                isinstance(hours_per_day, (int, float)), hours_per_day > 0,
                isinstance(total_minutes, (int, float)), total_minutes > 0]):
        logging.warning(f"Invalid inputs for get_task_breakdown. days_per_week: {days_per_week}, hours_per_day: {hours_per_day}, total_minutes: {total_minutes}. Using simple breakdown.")
        return generate_simple_breakdown(description, total_minutes, days_per_week, hours_per_day)

    # Calculate how many days the task will take (used for AI prompt context)
    hours_per_day_minutes = hours_per_day * 60
    total_hours_needed = total_minutes / 60
    effective_total_days_needed = max(0.1, total_hours_needed / hours_per_day)  # Ensure total_days_needed is at least 0.1
    days_needed = max(1, round(effective_total_days_needed))
    
    # System prompt for task breakdown - beginner focused
    system_prompt = """You are a task planning assistant specializing in breaking down tasks for BEGINNERS.

    IMPORTANT: Your response must be valid JSON array format. Start with [ and end with ]. Each object must have "step", "percentage", and "summary" fields.

    Format your response exactly like this:
    [
        {"step": "Step 1: Learning Basics", "percentage": 25, "summary": "Research fundamentals, understand terminology, and gather learning resources"},
        {"step": "Step 2: Setup & Preparation", "percentage": 20, "summary": "Install tools, configure environment, and prepare workspace"},
        {"step": "Step 3: Initial Practice", "percentage": 30, "summary": "Follow tutorials, practice basic concepts, make and fix beginner mistakes"},
        {"step": "Step 4: Implementation", "percentage": 20, "summary": "Apply learned skills to complete the actual task"},
        {"step": "Step 5: Review & Polish", "percentage": 5, "summary": "Test, debug, refine, and finalize the work"}
    ]
    
    BEGINNER-FOCUSED BREAKDOWN RULES:
    - Always include learning/research phases for beginners
    - Account for setup and configuration challenges
    - Include time for practice and making mistakes
    - Add troubleshooting and debugging steps
    - Provide 3-6 logical steps that make sense for a complete beginner
    - The percentage should add up to 100% and represent the proportion of total time
    - Each summary should describe beginner-friendly activities
    - Be specific to the actual task described
    - Focus on learning progression and skill building
    - Return ONLY the JSON array, no other text
    
    Examples:
    - For "learn coding": Planning (research languages, set up environment), Practice (tutorials, exercises), Projects (build applications)
    - For "plan party": Planning (guest list, venue, budget), Preparation (book venue, order supplies), Execution (setup, host event)
    - For "write report": Research (gather data, analyze), Writing (draft sections, compile), Review (edit, format, finalize)
    """
    
    # User prompt with task details - beginner focused
    user_prompt = f"""
    Task description: {description}
    Total estimated time: {total_hours_needed:.1f} hours ({total_minutes} minutes)
    Target audience: COMPLETE BEGINNER
    
    Break this task down into 3-6 logical steps/phases for someone who has never done this before.
    Include learning phases, setup steps, practice time, and troubleshooting.
    Make sure the summaries are specific to the actual task: "{description}"
    The percentages should add up to 100%.
    Consider that beginners need extra time for:
    - Understanding concepts and terminology
    - Setting up tools and environments
    - Making and fixing mistakes
    - Following tutorials and guides
    - Asking for help and research
    """
    
    # Prepare payload for OpenRouter API
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,  # Higher temperature for creative responses
        "max_tokens": 1500   # Increased max_tokens for potentially longer breakdowns
    }
    
    try:
        logging.info(f"Requesting task breakdown from model: {model}")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=45)
        
        if response.status_code == 200:
            result = response.json()
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logging.info(f"Raw breakdown response from {model}: {text[:150]}...")
            
            try:
                import re
                
                # First, try to find a JSON array in the response
                json_match = re.search(r'\[\s*(?:\{.*?\}\s*,?\s*)*\]', text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    # Clean up the response text and try to fix common JSON issues
                    json_str = text.strip().lstrip("```json").rstrip("```").strip()
                    
                    # If response doesn't start with [, try to wrap it as an array
                    if not json_str.startswith('['):
                        # Try to find individual step objects and wrap them in an array
                        if '{' in json_str and '}' in json_str:
                            # Split by closing brace followed by comma and try to fix
                            parts = re.split(r'\},\s*(?=\{|")', json_str)
                            fixed_parts = []
                            for i, part in enumerate(parts):
                                part = part.strip()
                                if part:
                                    # Ensure part starts with {
                                    if not part.startswith('{'):
                                        part = '{' + part
                                    # Ensure part ends with }
                                    if not part.endswith('}'):
                                        part = part + '}'
                                    # Fix missing "step" key by adding it if needed
                                    if '"step"' not in part and '"Step' in part:
                                        part = part.replace('"Step', '"step": "Step')
                                    fixed_parts.append(part)
                            json_str = '[' + ','.join(fixed_parts) + ']'
                        else:
                            logging.warning(f"Could not extract a clear JSON from {model} response. Attempting fallback.")
                            raise ValueError("No valid JSON structure found")
                
                logging.info(f"Attempting to parse JSON: {json_str[:200]}...")
                breakdown_list = json.loads(json_str)
                
                if not isinstance(breakdown_list, list) or not all(isinstance(item, dict) and \
                                                                   'percentage' in item and \
                                                                   'summary' in item for item in breakdown_list):
                    logging.error(f"Parsed JSON from {model} is not a list of valid breakdown dictionaries: {breakdown_list}")
                    raise ValueError("Parsed JSON is not a list of valid breakdown dictionaries.")

                logging.info(f"Successfully generated AI breakdown with {len(breakdown_list)} steps using {model}")
                return breakdown_list
                
            except (json.JSONDecodeError, ValueError) as e:
                logging.error(f"Error parsing or validating breakdown JSON from {model}: {str(e)}. Response text: '{text}'. Falling back to simple breakdown.")
                return generate_simple_breakdown(description, total_minutes, days_per_week, hours_per_day)
            except Exception as e:
                logging.error(f"Unexpected error processing breakdown response from {model}: {str(e)}. Falling back to simple breakdown.")
                return generate_simple_breakdown(description, total_minutes, days_per_week, hours_per_day)
        else:
            logging.error(f"API request for breakdown to {model} failed with status {response.status_code}: {response.text}. Falling back to simple breakdown.")
            return generate_simple_breakdown(description, total_minutes, days_per_week, hours_per_day)
            
    except requests.exceptions.Timeout:
        logging.error(f"Timeout during API request for breakdown to {model}. Falling back to simple breakdown.")
        return generate_simple_breakdown(description, total_minutes, days_per_week, hours_per_day)
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception during API call for breakdown to {model}: {str(e)}. Falling back to simple breakdown.")
        return generate_simple_breakdown(description, total_minutes, days_per_week, hours_per_day)
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_task_breakdown with {model}: {str(e)}. Falling back to simple breakdown.")
        return generate_simple_breakdown(description, total_minutes, days_per_week, hours_per_day)


def create_default_breakdown(total_hours: float, hours_per_day: float, days_needed: int) -> List[Dict]:
    """DEPRECATED: This function is no longer used. Use generate_simple_breakdown instead."""
    logging.warning("create_default_breakdown is deprecated and should not be called.")
    total_minutes_approx = total_hours * 60
    return generate_simple_breakdown("Default task (from deprecated function)", int(total_minutes_approx), None, hours_per_day)


def estimate_time(description: str, days_per_week: int = None, hours_per_day: float = None) -> Tuple[int, List[Dict]]:
    """
    Estimate time required for a task using OpenRouter API and generate a breakdown
    
    Args:
        description: The task description
        days_per_week: Number of days per week available for the task
        hours_per_day: Number of hours per day available for the task
        
    Returns:
        Tuple of (estimated minutes, task breakdown list)
    """
    logging.info(f"Starting task time estimation for: '{description[:50]}...'")
    
    minutes = None
    for model in AVAILABLE_MODELS:
        try:
            logging.info(f"Trying estimation with model: {model}")
            minutes = get_time_estimate(description, model)
            
            if minutes is not None:
                logging.info(f"Successfully estimated {minutes} minutes using {model}")
                break
            
            logging.warning(f"Model {model} failed to provide a valid estimate. Trying next model...")
            time.sleep(1)
            
        except Exception as e:
            logging.error(f"Unhandled error with model {model} in estimate_time loop: {str(e)}")
            continue
    
    if minutes is None:
        logging.warning("All models failed to provide an estimate. Using heuristic estimation.")
        
        word_count = len(description.split())
        
        if "meeting" in description.lower() or "call" in description.lower():
            minutes = 30
        elif "email" in description.lower() or "message" in description.lower():
            minutes = 10
        elif word_count <= 3:
            minutes = 15
        elif word_count <= 8:
            minutes = 30
        elif word_count <= 15:
            minutes = 60
        else:
            minutes = 90
        
        logging.info(f"Heuristic estimated {minutes} minutes based on description length and keywords")
    
    breakdown = None
    if minutes is not None and minutes > 0:
        try:
            logging.info(f"Generating task breakdown for {minutes} minutes")
            # Use default values if days_per_week or hours_per_day are None
            effective_days_per_week = days_per_week if days_per_week is not None else 5
            effective_hours_per_day = hours_per_day if hours_per_day is not None else 2.0
            
            breakdown = get_task_breakdown(description, minutes, effective_days_per_week, effective_hours_per_day)
            if not breakdown:
                logging.warning("Task breakdown generation failed, creating a simple default.")
                # Create a simple fallback breakdown
                breakdown = [
                    {"step": "Step 1: Planning", "percentage": 25, "summary": "Research, planning, and preparation"},
                    {"step": "Step 2: Implementation", "percentage": 60, "summary": "Main execution and work"},
                    {"step": "Step 3: Review", "percentage": 15, "summary": "Testing, review, and finalization"}
                ]
        except Exception as e:
            logging.error(f"Error generating task breakdown: {str(e)}")
            # Create a simple fallback breakdown
            breakdown = [
                {"step": "Step 1: Planning", "percentage": 25, "summary": "Research, planning, and preparation"},
                {"step": "Step 2: Implementation", "percentage": 60, "summary": "Main execution and work"},
                {"step": "Step 3: Review", "percentage": 15, "summary": "Testing, review, and finalization"}
            ]
    elif minutes is None or minutes <= 0:
        logging.info(f"Skipping breakdown generation as estimated minutes is {minutes}.")
        return minutes, []  # Return empty list for breakdown

    return minutes, breakdown
