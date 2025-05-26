import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_simple_breakdown(
    description: str,
    total_minutes: int,
    days_per_week: Optional[int],
    hours_per_day: Optional[float]
) -> List[Dict]:
    """
    Generates a structured, day-by-day breakdown for a task.

    Args:
        description: The description of the task.
        total_minutes: Total estimated minutes for the task.
        days_per_week: How many days a week are available for work.
        hours_per_day: How many hours per day are available for work.

    Returns:
        A list of dictionaries, where each dictionary represents a day's work,
        or an empty list if breakdown cannot be generated.
    """
    if not all([description, isinstance(total_minutes, (int, float))]):
        logging.warning("generate_simple_breakdown: Invalid base inputs (description or total_minutes).")
        return []

    if total_minutes <= 0:
        logging.info("generate_simple_breakdown: Total minutes is zero or less, no breakdown to generate.")
        return []

    if days_per_week is None or hours_per_day is None:
        logging.info("generate_simple_breakdown: days_per_week or hours_per_day not provided. Cannot generate daily breakdown.")
        # Return a single entry if only total_minutes is known and positive
        return [{
            "day": "Task",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "hours": round(total_minutes / 60, 1),
            "summary": f"Complete task: {description}"
        }]

    if not (isinstance(days_per_week, (int, float)) and days_per_week > 0 and
            isinstance(hours_per_day, (int, float)) and hours_per_day > 0):
        logging.warning(f"generate_simple_breakdown: Invalid days_per_week ({days_per_week}) or hours_per_day ({hours_per_day}).")
        # Fallback to a single entry
        return [{
            "day": "Task",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "hours": round(total_minutes / 60, 1),
            "summary": f"Complete task: {description}"
        }]

    logging.info(f"Generating simple breakdown for '{description[:30]}...' ({total_minutes} min, {days_per_week}dw, {hours_per_day}hd)")

    breakdown_list: List[Dict] = []
    
    minutes_per_work_day = hours_per_day * 60
    if minutes_per_work_day == 0: # Should be caught by hours_per_day > 0 check, but as safeguard
        logging.warning("generate_simple_breakdown: minutes_per_work_day is zero, cannot generate breakdown.")
        return []

    # Calculate the number of workdays needed.
    # Ensure at least one day if there are any minutes.
    num_total_work_days = math.ceil(total_minutes / minutes_per_work_day) if total_minutes > 0 else 0
    if num_total_work_days == 0 and total_minutes > 0 : # e.g. 10 minutes task, 8 hours per day -> num_total_work_days = 1
        num_total_work_days = 1


    remaining_minutes = float(total_minutes)
    current_date = datetime.now()
    day_count_actual = 0 # Actual work days in the breakdown

    for i in range(int(num_total_work_days)):
        if remaining_minutes <= 0:
            break

        if days_per_week <= 0 or days_per_week > 7 : # Treat invalid days_per_week as continuous work
            pass # No weekend skipping
        elif days_per_week < 7 : # Standard 1-7 days
             # Skip weekends if days_per_week indicates a work week (e.g., 5 days)
            effective_days_per_week = int(days_per_week)
            if effective_days_per_week <= 5: # Common case: Monday-Friday
                while current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                    current_date += timedelta(days=1)
            # For 6 days a week, one might skip just Sunday, or it might be flexible.
            # This simple model assumes work on the first 'effective_days_per_week' days it encounters.
            # A more complex model would need specific off-days.
            # For now, if days_per_week is 6, it will just run for 6 days then skip one if it lands on Sunday by chance.
            # This part could be refined if more specific weekend/off-day rules are needed.

        minutes_for_today = min(remaining_minutes, minutes_per_work_day)
        
        summary_text = f"Work on: {description} (Part {day_count_actual + 1})"
        if num_total_work_days == 1 or remaining_minutes == minutes_for_today : # If it's the only day or the last day of work
             summary_text = f"Complete task: {description}" if num_total_work_days == 1 else f"Final work on: {description} (Part {day_count_actual + 1})"


        breakdown_list.append({
            "day": f"Day {day_count_actual + 1}",
            "date": current_date.strftime("%Y-%m-%d"),
            "hours": round(minutes_for_today / 60, 1),
            "summary": summary_text
        })

        remaining_minutes -= minutes_for_today
        current_date += timedelta(days=1)
        day_count_actual += 1
        
        if day_count_actual >= 365 * 2: # Safety break for very long tasks / small hours_per_day
            logging.warning("generate_simple_breakdown: Exceeded 2 years of daily tasks, breaking.")
            break

    if not breakdown_list and total_minutes > 0: # Ensure at least one entry if there was work but loop didn't run
        logging.warning("generate_simple_breakdown: Breakdown list is empty but total_minutes > 0. Creating a single entry.")
        return [{
            "day": "Task",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "hours": round(total_minutes / 60, 1),
            "summary": f"Complete task: {description}"
        }]
        
    return breakdown_list

