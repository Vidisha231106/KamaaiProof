# Frontend Source Overview

This folder contains application source code for the React user interface.

## File and Folder Roles

- `App.jsx`: route composition and application shell integration
- `main.jsx`: React app bootstrap
- `styles.css`: global design system and theme styles
- `components/`: reusable UI components
- `pages/`: route-level page views
- `services/`: API and data normalization helpers

## Data Flow Summary

1. User uploads and tags documents in pages layer.
2. Services layer sends request to backend parse endpoint.
3. Services layer normalizes response.
4. Result page and components render normalized data.

## Editing Guidelines for AI Agents

1. Keep page logic in pages and shared widgets in components.
2. Keep API and payload transforms in services.
3. Preserve dual-theme compatibility after any style change.
4. Validate route behavior after modifying App or page files.
