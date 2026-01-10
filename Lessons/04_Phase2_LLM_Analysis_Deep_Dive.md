# Lesson 04 - Phase 2: LLM Analysis Deep Dive

The LLM analysis phase transforms normalized events into structured findings.
This project supports multiple providers and uses source-specific prompts.

## Objectives
- Understand provider and model selection
- Learn how batching controls cost and reliability
- See how prompts differ by source

## Providers and models
- Supported providers: Gemini and OpenAI
- CLI flags: `--provider` and `--model`
- Environment: `GEMINI_API_KEY` or `OPENAI_API_KEY`
- Default model: `gemini-flash-latest`

## Source-specific prompts
The prompt is chosen based on the source detected during ingest:
- Windows prompts emphasize process creation and command-line analysis
- AWS prompts emphasize identity, API calls, and account context
- GCP prompts emphasize audit logs, IAM activity, and service usage

## Batching strategy
Batching keeps each request within practical limits:
- Windows: up to 50 events or ~24k characters per batch
- AWS: 25 events per batch (config driven)
- GCP: chunked processing for large log sets

## Reliability
- Each batch is attempted up to three times
- Failures are surfaced in the final report
- Validation runs after LLM output to enforce schema correctness

## Deterministic additions
GCP analysis includes deterministic IOC extraction in addition to LLM results
to improve consistency for common indicators.

## Exercises
1. Change the Windows batch size and observe how it affects run time and cost.
2. Update a prompt to add a new detection rule and see how it changes output.
