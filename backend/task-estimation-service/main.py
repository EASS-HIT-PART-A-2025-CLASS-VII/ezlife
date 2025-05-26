from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
import logging
import os

# Import your estimator functions
from ai_estimator import estimate_time as ai_estimate_time, OPENROUTER_API_KEY
from fallback_estimator import fallback_estimate_time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="Task Estimation Service",
    description="Provides AI-based and fallback task time estimations and breakdowns.",
    version="0.2.0"
)

class TaskEstimationRequest(BaseModel):
    description: str = Field(..., example="Plan a company offsite event for 50 people")
    days_per_week: Optional[int] = Field(None, example=5, description="Number of days per week available for the task")
    hours_per_day: Optional[float] = Field(None, example=2.0, description="Number of hours per day available for the task")

class TaskEstimationResponse(BaseModel):
    estimated_minutes: int
    breakdown: Optional[List[Dict]] = None
    source: str # 'ai' or 'fallback'

@app.post("/estimate_time", response_model=TaskEstimationResponse)
async def estimate_task_time(request: TaskEstimationRequest):
    """
    Estimate the time required for a task and provide a breakdown.
    Uses AI estimation first, then falls back to a simpler heuristic if AI fails
    or the API key is not available.
    """
    description = request.description
    days_per_week = request.days_per_week
    hours_per_day = request.hours_per_day
    
    logging.info(f"Received estimation request for: '{description[:50]}...'")

    estimated_minutes: Optional[int] = None
    task_breakdown: Optional[List[Dict]] = None
    source: str = "unknown" # Initialize source

    try:
        if OPENROUTER_API_KEY:
            logging.info("Attempting AI estimation.")
            estimated_minutes, task_breakdown = ai_estimate_time(description, days_per_week, hours_per_day)
            if estimated_minutes is not None:
                source = "ai"
                logging.info(f"AI estimation result: {estimated_minutes} minutes.")
            else:
                logging.warning("AI estimation returned None, will proceed to fallback.")
        else:
            logging.warning("OPENROUTER_API_KEY not found. Skipping AI estimation.")

        # If AI estimation failed (returned None) or wasn't attempted, use fallback
        if estimated_minutes is None:
            logging.warning("AI estimation failed or was skipped. Using fallback estimator.")
            estimated_minutes, task_breakdown = fallback_estimate_time(description, days_per_week, hours_per_day)
            source = "fallback"
            logging.info(f"Fallback estimation result: {estimated_minutes} minutes.")
            
        if estimated_minutes is None: # Should not happen if fallback works, but as a safeguard
            logging.error("Both AI and fallback estimators failed to provide an estimate.")
            # Ensure source reflects the last attempt if it got this far
            raise HTTPException(status_code=500, detail="Failed to estimate task time using all available methods.")

        return {
            "estimated_minutes": estimated_minutes,
            "breakdown": task_breakdown if task_breakdown else [],
            "source": source
        }
        
    except HTTPException as http_exc: # Re-raise HTTPExceptions
        raise http_exc
    except Exception as e:
        logging.error(f"Unexpected error in estimate_task_time endpoint: {str(e)}", exc_info=True)
        # Fallback in case of any unexpected error during the primary logic
        try:
            logging.warning("Unexpected error occurred. Attempting final fallback estimation.")
            estimated_minutes, task_breakdown = fallback_estimate_time(description, days_per_week, hours_per_day)
            if estimated_minutes is not None:
                return {
                    "estimated_minutes": estimated_minutes,
                    "breakdown": task_breakdown if task_breakdown else [],
                    "source": "fallback_exception_handler"
                }
            else:
                 raise HTTPException(status_code=500, detail=f"Internal server error after attempting final fallback: {str(e)}")
        except Exception as final_e:
            logging.critical(f"Critical error: Final fallback also failed: {str(final_e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error, and final fallback failed: {str(final_e)}")

@app.get("/health", summary="Health Check", description="Returns the status of the service.")
async def health_check():
    """Basic health check endpoint."""
    logging.info("Health check endpoint called.")
    # More comprehensive checks could be added here:
    # - Check API key presence (but not validity to avoid leaking info)
    # - Check connectivity to external services (if any, though OpenRouter is on-demand)
    # - Check basic functionality (e.g., a quick self-test of an estimator with a dummy task)
    return {"status": "healthy", "version": app.version, "ai_service_configured": bool(OPENROUTER_API_KEY)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) # Port for task-estimation-service
