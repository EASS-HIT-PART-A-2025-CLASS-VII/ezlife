# AI Task Estimator

## Overview
The AI Task Estimator is a component of the EZlife Task Management application that automatically estimates how much time a task will take based on its description. This service uses OpenRouter to connect to various Large Language Models (LLMs) to generate time estimates.

## How It Works

1. When a user creates a new task without specifying an estimated time, the backend automatically calls the AI estimator.
2. The estimator sends the task description to the OpenRouter API, which connects to a free LLM.
3. The LLM analyzes the task description and returns an estimated time in minutes.
4. If the primary model fails, the estimator tries alternative models in sequence.
5. As a last resort, the system uses a simple heuristic based on word count and keywords.

## Models Used

The AI estimator tries these models in order:

1. `mistralai/mistral-7b-instruct` - Primary model (Mistral 7B)
2. `google/palm-2-chat-bison` - First fallback (PaLM 2)
3. `anthropic/claude-instant-v1` - Second fallback (Claude Instant)
4. `openai/gpt-3.5-turbo` - Last resort (GPT-3.5)

## Usage

In the frontend, leave the "Estimated minutes" field blank when creating a task to have the AI automatically estimate the time required. A spinner will appear while the AI is generating the estimate.

## Configuration

The AI estimator is configured with the following:

- **API Key**: Stored in the `OPENROUTER_API_KEY` variable
- **API URL**: OpenRouter API endpoint for chat completions
- **System Prompt**: Instructions for the AI to respond with a numerical estimate only
- **Temperature**: Set to 0.1 for consistent responses
- **Max Tokens**: Limited to 10 as we only need a short numerical answer

## Error Handling

The estimator includes robust error handling:
- Multiple model fallbacks if the primary model fails
- Timeout handling to prevent long waits
- Sanity checks on estimated times (capping extremely long estimates)
- Heuristic fallback if all AI models fail

## Frontend Integration

The TaskPage component in the frontend shows a spinner when the AI is estimating a task's time, providing visual feedback to the user during the estimation process.
