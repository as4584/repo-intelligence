# ADR 0001: Product direction

## Status

Accepted

## Decision

Build Change Radar as a local-first change preflight and working-set recommender for AI-assisted code edits.

## Why

The repo research consistently points to a narrow but valuable gap:

- AI tools lack reliable repo scoping
- developers do not know what files to include or inspect
- blast radius is useful only if grounded in a current change workflow

This wedge is more differentiated than a generic repo graph viewer and more sustainable than a tiny one-off hack.

## Consequences

### We will do

- prioritize working-set ranking and diff preflight
- keep output deterministic and explainable
- keep the first product local-first
- start with CLI and MCP

### We will not do now

- build a generic chat product
- compete on code generation
- build cloud infra
- build a graph-heavy platform too early
