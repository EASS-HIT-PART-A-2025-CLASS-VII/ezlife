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

# Load environment variables from .env file
load_dotenv()

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    logging.warning("OPENROUTER_API_KEY not found in environment variables. AI estimator will likely fail.")

# Available models to try in order (fallback mechanism)
AVAILABLE_MODELS = [
    "mistralai/mistral-7b-instruct",  # First choice - Mistral 7B Instruct
    "google/palm-2-chat-bison",        # Second choice - Palm 2
    "anthropic/claude-instant-v1",     # Third choice - Claude Instant
    "openai/gpt-3.5-turbo"             # Last resort - GPT 3.5 (uses credits)
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
    # System prompt to guide the model's response format
    system_prompt = "You are a task time estimation assistant. Respond ONLY with a numerical estimate in minutes for how long the task would take an average person. Give a single number only, no explanations or additional text."
    
    # User prompt with the task description
    user_prompt = f"How many minutes would it take to complete this task: {description}"
    
    # Prepare payload for OpenRouter API (following OpenAI format)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,  # Low temperature for more consistent responses
        "max_tokens": 10     # We only need a small number
    }
    
    logging.info(f"Requesting estimation from model: {model} for task: '{description[:50]}...'")
    
    try:
        # Make API request
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=15)  # Increased timeout
        
        if response.status_code == 200:
            result = response.json()
            # Extract the response text from the completion
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            logging.info(f"Raw response from {model}: {text}")
            
            # Extract numbers from the response
            digits = ''.join(filter(str.isdigit, text))
            if digits:
                minutes = int(digits)
                # Sanity check - if estimate is absurdly high, cap it
                if minutes > 1440 * 3:  # More than 3 days in minutes
                    logging.warning(f"Absurdly high estimate ({minutes} min) from {model} capped to 120 min.")
                    minutes = 120    # Cap at 2 hours
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
    
    # Validate inputs before proceeding
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
    
    # System prompt for task breakdown
    system_prompt = """You are a task planning assistant. Break down the given task into daily chunks with specific
    summaries of what should be done each day. Format your response as JSON with the following structure:
    [
        {"day": "Day 1", "hours": hours_for_day_1, "summary": "specific subtasks for day 1"},
        {"day": "Day 2", "hours": hours_for_day_2, "summary": "specific subtasks for day 2"}
    ]
    
    The hours should add up to the total hours needed for the task, and be distributed according to the hours_per_day limit.
    Each summary should be detailed, specific and actionable - describing concrete subtasks to work on, milestones to accomplish,
    and specific outcomes expected for that day's work. Be practical and realistic about what can be accomplished in the given time.
    
    Consider the logical progression of the task - what needs to be done first, what depends on earlier work, and how to sequence
    the work efficiently. Include appropriate time for planning, review, and any necessary communication or coordination.
    """
    
    # User prompt with task details
    user_prompt = f"""
    Task description: {description}
    Total estimated hours: {total_hours_needed:.1f} hours
    Days per week: {days_per_week}
    Hours per day: {hours_per_day}
    
    Break this down into {days_needed} days of work, with each day having at most {hours_per_day} hours.
    Make sure the summaries are specific to the task described.
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
                json_match = re.search(r'\[\s*(?:\{.*?\}\s*,?\s*)*\]', text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = text.strip().lstrip("```json").rstrip("```").strip()
                    if not (json_str.startswith('[') and json_str.endswith(']')):
                        logging.warning(f"Could not extract a clear JSON array from {model} response. Attempting to parse as is.")
                
                breakdown_list = json.loads(json_str)
                
                if not isinstance(breakdown_list, list) or not all(isinstance(item, dict) and \
                                                                   'day' in item and 'date' in item and \
                                                                   'hours' in item and 'summary' in item for item in breakdown_list):
                    logging.error(f"Parsed JSON from {model} is not a list of valid breakdown dictionaries: {breakdown_list}")
                    raise ValueError("Parsed JSON is not a list of valid breakdown dictionaries.")

                logging.info(f"Successfully generated AI breakdown with {len(breakdown_list)} days using {model}")
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
    if days_per_week is not None and hours_per_day is not None and minutes is not None and minutes > 0:
        try:
            if not (isinstance(days_per_week, (int, float)) and days_per_week > 0 and 
                    isinstance(hours_per_day, (int, float)) and hours_per_day > 0):
                logging.warning(f"Invalid days_per_week ({days_per_week}) or hours_per_day ({hours_per_day}). Skipping breakdown.")
            else:
                logging.info(f"Generating task breakdown for {minutes} minutes over {days_per_week} days/week and {hours_per_day} hours/day")
                breakdown = get_task_breakdown(description, minutes, int(days_per_week), float(hours_per_day))
                if not breakdown:
                    logging.warning("Task breakdown generation failed, creating a simple default.")
                    total_hours = minutes / 60
                    breakdown = [generate_simple_breakdown(description, minutes, days_per_week, hours_per_day)]
        except Exception as e:
            logging.error(f"Error generating task breakdown: {str(e)}")
            total_hours = minutes / 60
            breakdown = [generate_simple_breakdown(description, minutes, days_per_week, hours_per_day)]
    elif minutes is None or minutes <= 0:
        logging.info(f"Skipping breakdown generation as estimated minutes is {minutes}.")
        return minutes, []  # Return empty list for breakdown

    return minutes, breakdown
