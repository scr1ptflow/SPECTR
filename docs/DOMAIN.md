# Elite Bridge Domain Model

## Purpose

This directory defines every entity used by Elite Bridge.

These files are the canonical source of truth for the application.

Every backend model, database table, REST endpoint, WebSocket message, and frontend interface must map to these definitions.

If an entity is not defined here, it does not exist.

---

## Goals

The domain model exists to:

- Eliminate duplicated definitions.
- Keep backend and frontend synchronized.
- Make AI-generated code consistent.
- Allow future code generation.
- Keep the project maintainable.

---

## Rules

Every entity contains:

- Purpose
- Owner
- Data Source
- Fields
- Relationships
- Events
- Used By
- Notes

Only these YAML files define entities.

No code should invent additional fields.

When changing an entity, update the corresponding YAML first.

The YAML files are considered part of the architecture.
