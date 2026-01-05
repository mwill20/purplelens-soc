# PurpleLens Documentation

This directory contains all documentation for the PurpleLens AI Security Analyst Assistant project.

## Directory Structure

### Core Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and 5-phase pipeline design
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md) - Demonstration walkthrough guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [Fallback.md](Fallback.md) - Fallback mechanisms and error handling
- [PurpleLens_SOC_Phase_2_Roadmap.md](PurpleLens_SOC_Phase_2_Roadmap.md) - Future enhancements roadmap
- [BASELINE_VERIFICATION_2026-01-02.md](BASELINE_VERIFICATION_2026-01-02.md) - Baseline test verification record

### Source-Specific Documentation

#### [aws/](aws/)
AWS CloudTrail integration documentation
- `ENHANCEMENT_1_NorthStar.md` - AWS CloudTrail Enhancement specification
- `BRANCH_STRATEGY.md` - AWS implementation branch strategy

#### [gcp/](gcp/)
Google Cloud Platform Audit Logs integration documentation
- `ENHANCEMENT_2_NorthStar.md` - GCP Mini-Lab Enhancement specification
- `MINILAB_PLAN.md` - Phase 0 Mini-Lab blueprint (8 events)
- `OVERSEER_APPROVAL.md` - Formal quality gate approval record
- `TECHNICAL_ADDENDUM.md` - Technical enhancement change log

#### [windows/](windows/)
Windows Event Log (EVTX) integration documentation
- *(Future: Windows-specific implementation guides)*

## Overseer Role
The `Overseer.md` file (if present in project root) defines the quality gate and phase approval process used throughout this project.

## Assets
- `PurpleLens-SOC-Logo.png` - Project logo
- `PurpleLens_SOC_Architecture.png` - Architecture diagram
- `Mental Model.png`, `mental model_*.jpg` - Conceptual diagrams
- `Cloud AI Security Engineer - Python Assignment - 1121 (2).pdf` - Original project brief
