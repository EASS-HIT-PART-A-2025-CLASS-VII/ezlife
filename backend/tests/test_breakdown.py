"""
Test the task breakdown functionality in the ai_estimator module
"""
from task_service.ai_estimator import estimate_time, get_task_breakdown

def test_estimation():
    """Test the task time estimation and breakdown"""
    description = "Build a simple to-do list app with React"
    days_per_week = 5
    hours_per_day = 3
    
    print(f"Testing estimation for task: {description}")
    print(f"Parameters: {days_per_week} days/week, {hours_per_day} hours/day\n")
    
    # Test full estimation with breakdown
    minutes, breakdown = estimate_time(description, days_per_week, hours_per_day)
    
    print(f"\n✅ Estimated minutes: {minutes}")
    print(f"✅ Generated {len(breakdown) if breakdown else 0} day breakdown\n")
    
    if breakdown:
        print("Task Breakdown:")
        for day in breakdown:
            print(f"- {day['day']} ({day['date']}): {day['hours']} hours")
            print(f"  {day['summary'][:80]}..." if len(day['summary']) > 80 else f"  {day['summary']}")
        
        print("\nFirst day summary sample:")
        print(breakdown[0]['summary'])
    
    return minutes, breakdown

if __name__ == "__main__":
    test_estimation()