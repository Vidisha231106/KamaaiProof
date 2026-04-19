# Frontend Components

This folder contains reusable presentational and interaction components shared across pages.

## Current Components

- Layout
- ThemeToggle
- LoadingSpinner
- LoanRealityCalculator

## Responsibilities

- Keep page files focused on flow logic.
- Encapsulate repeated UI patterns.
- Preserve visual consistency across themes.
- Keep components small and composable.

## Component Notes

### Layout

- Wraps all route pages.
- Owns top navigation shell placement.
- Renders theme switcher.

### ThemeToggle

- Switches between white/navy and black/white themes.
- Persists selected theme in local storage.

### LoadingSpinner

- Standard inline loading indicator for API actions.

### LoanRealityCalculator

- Accepts user loan input in rupees.
- Calculates moneylender repayment and MFI repayment.
- Displays worker savings in rupees only.

## Editing Rules for AI Agents

1. Avoid introducing tight coupling between components and backend payloads.
2. Keep props explicit and documented.
3. Preserve keyboard and screen-reader usability.
4. Keep style changes aligned with dual-theme contrast goals.