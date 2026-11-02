# Correctness and Calibration Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan inline. Steps use checkbox syntax for tracking.

**Goal:** Resolve known workout inconsistencies and stop categorical recovery or race conclusions from exceeding their evidence.

**Architecture:** Keep canonical Markdown routing and MCP contracts. Retain existing workout steps and identify their actual default volume. Reuse structured readiness for wellness interpretation; assess race preparation separately from today's recovery.

**Tech Stack:** Markdown; existing shell validators; synthetic agent scenarios.

**Spec:** `docs/superpowers/specs/2026-11-02-coaching-methodology-exploration.md`, sections 1–2. The user's instruction to continue authorizes this first slice.

## Decisions

- Correct metadata to actual written defaults rather than silently adding workout volume. Larger sessions require explicit parameterization and new totals.
- Define running EF with speed units and preserve contextual comparison limits.
- Keep single-target guidance; replace the pace target in HR-based strides with a qualitative acceleration cue.
- Use compact readiness as the advisory wellness assessment, preserving confidence and baseline provenance. Raw-only wellness produces observations without inventing a competing readiness score.
- Remove unsourced CTL completion thresholds and universal race-day TSB bands. Use goal/date/course context and race-specific evidence, with an explicit insufficient-evidence outcome.
- Treat load and recovery heuristics as prompts for context, not diagnoses. No new physiological thresholds.

## Global Constraints

- Separate swim, bike, and run.
- Preserve MCP evidence provenance and explicit write approval.
- No live athlete writes, server changes, or deployment.
- Update only canonical skill sources; the retired ChatGPT mirror remains retired.

## Tasks

- [x] Capture baseline synthetic behavior for date-sensitive race readiness, missing swim evidence, conflicting fatigue signals, CSS volume, and EF direction.
- [x] Correct default workout metadata and define total-expansion rules; clarify EF and target consistency.
- [x] Revise recovery rules, wellness routing, and race-readiness output around contextual evidence and uncertainty.
- [x] Rerun the same scenarios with a fresh agent; record observed outcomes separately from expected behavior.
- [x] Run both existing validators and diff checks, review the changed guidance, and commit.

## Review Focus

- Unknown race date must not become an implied race-today assessment.
- Missing essential discipline evidence must prevent an overall supported verdict.
- Positive TSB must not override sparse recent training or athlete symptoms.
- Advertised default totals must agree with expanded steps.
- A simulated coaching check must never be reported as live scheduling proof.

Progression, adaptive planning, shared response structure, and installation refresh follow in separate slices after this foundation.
