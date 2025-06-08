# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the FluentPro backend project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences.

## ADR Format

Each ADR follows this structure:

- **Title**: ADR-XXX: Brief descriptive title
- **Status**: Draft | Proposed | Accepted | Deprecated | Superseded
- **Context**: What is the issue that we're seeing that is motivating this decision or change?
- **Decision**: What is the change that we're proposing and/or doing?
- **Consequences**: What becomes easier or more difficult to do because of this change?
- **References**: Links to related documentation or resources

## Current ADRs

- [ADR-001: Use Domain-Driven Design](001-use-ddd.md)
- [ADR-002: Async-First Architecture](002-async-first.md)

## Creating a New ADR

1. Copy the template from an existing ADR
2. Number it sequentially (e.g., 003, 004, etc.)
3. Fill in all sections with relevant information
4. Set status to "Proposed" initially
5. After review and approval, change status to "Accepted"