"""
Test the fallback estimator
"""
from task_service.fallback_estimator import estimate_time_fallback, generate_task_breakdown

def test_fallback():
    """Test the fallback estimator"""
    description = "Create a presentation for the quarterly review meeting"
    days_per_week = 5
    hours_per_day = 2
    
    print(f"Testing fallback estimation for: {description}")
    estimated_minutes, breakdown = estimate_time_fallback(
        description, days_per_week=days_per_week, hours_per_day=hours_per_day
    )
    
    print(f"Estimated minutes: {estimated_minutes}")
    print(f"Generated breakdown with {len(breakdown)} days")
    
    if breakdown:
        print("\nTask Breakdown:")
        for day in breakdown:
            print(f"- {day['day']} ({day['date']}): {day['hours']} hours")
            print(f"  {day['summary'][:100]}..." if len(day['summary']) > 100 else f"  {day['summary']}")
    
    return estimated_minutes, breakdown

if __name__ == "__main__":
    test_fallback()
