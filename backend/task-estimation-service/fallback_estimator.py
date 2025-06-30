"""
Fallback implementation for task breakdown without relying on external APIs
"""
import logging
from typing import List, Dict, Tuple, Optional
from breakdown_utils import generate_simple_breakdown  

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fallback_estimate_time(description: str, days_per_week: Optional[int] = None, hours_per_day: Optional[float] = None) -> Tuple[Optional[int], List[Dict]]:
    """
    Fallback estimation logic if AI service fails or is unavailable.
    Provides a very basic heuristic based on description length and keywords.
    Generates a breakdown using the utility function.
    """
    logging.info(f"Using fallback estimator for task: '{description[:50]}...'")
    
    if not description:
        logging.warning("Fallback estimator: Description is empty. Cannot estimate.")
        return None, []

    # Estimate time based on description length and complexity
    words = description.split()
    word_count = len(words)
    
    # Base estimate on word count
    if word_count <= 3:
        minutes = 15  # Very short descriptions
    elif word_count <= 8:
        minutes = 30  # Short descriptions
    elif word_count <= 15:
        minutes = 60  # Medium descriptions
    else:
        minutes = 90  # Long descriptions
    
    # Adjust based on keywords
    description_lower = description.lower()
    if any(word in description_lower for word in ["meeting", "call", "discuss"]):
        minutes = max(30, minutes)
    elif any(word in description_lower for word in ["email", "message", "reply"]):
        minutes = min(15, minutes)
    elif any(word in description_lower for word in ["report", "presentation", "document", "project"]):
        minutes = max(120, minutes)
    elif any(word in description_lower for word in ["analyze", "research", "study", "investigate"]):
        minutes = max(90, minutes)
    
    # Ensure minutes is at least 5
    minutes = max(5, minutes)
    
    logging.info(f"Fallback estimated {minutes} minutes for '{description[:50]}...'")
    
    breakdown: List[Dict] = []  # Initialize with an empty list
    if minutes > 0:
        try:
            # Use the centralized breakdown utility
            breakdown = generate_simple_breakdown(description, minutes, days_per_week, hours_per_day)
            logging.info(f"Fallback breakdown generated with {len(breakdown)} entries.")
        except Exception as e:
            logging.error(f"Error generating fallback task breakdown using utility: {str(e)}")
            # If utility fails, provide a minimal single-entry breakdown as a last resort
            breakdown = [{
                "day": "Task",
                "date": "N/A",  # Date might not be calculable if utility failed badly
                "hours": round(minutes / 60, 1),
                "summary": f"Complete task: {description}"
            }]
    elif minutes <= 0:
        logging.info(f"Skipping fallback breakdown generation as estimated minutes is {minutes}.")

    return minutes, breakdown
