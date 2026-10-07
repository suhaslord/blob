# CareRoute

CareRoute helps people find affordable US care resources and prepare questions for a medical visit. It is an educational prototype, not a diagnosis or clinical triage tool.

## Run locally

Use Node 22.13+ or 24. Run `npm ci`, `npm run dev`, `npm run build`, and `npm test`. Vite serves the app; Vercel hosts the verified static build. No API keys are needed.

## Architecture and privacy

React and TypeScript hold the checklist, chosen tool, and concern in component state. Nothing entered is sent to an application server, logged, or persisted. There is no database schema because this release has no database. Reloading or pressing Clear removes the draft. Static hosting still receives normal HTTP requests for assets.

A multinomial naive Bayes model is trained at module initialization on 24 hand-written synthetic phrases in three classes. It may suggest an affordable-care or visit-preparation tool. Users explicitly apply a suggestion. Unknown or weak matches abstain. The model never determines diagnosis, medical urgency, or emergency actions; the separate warning checklist always takes priority. This small English-only dataset is a demonstration, not a validated language or medical model.

## Verification

The build includes TypeScript checking. Model tests exercise six held-out administrative phrases and six abstention inputs. Browser verification checks all 15 warning combinations in each of the three modes (45 combinations), links, escaped text, result focus, stale-plan removal, reset, four viewport sizes, browser errors, outgoing requests, and storage. The first verified run passed 56 checks. Only synthetic text was used.

Try selecting a physical emergency together with the crisis warning: 911 must remain the main action, with 988 shown as additional crisis support. Any selected warning appears immediately, before pressing Build. No selected warning does not imply that a condition is safe.

## Provenance and contributions

Suhas Beemineni's original CareRoute interface was recovered from source revision b9fc7ed621e491ab6372deb40a572a194433b597. The October 6 work migrated hosting to Vercel, added the on-device model, fixed mixed warning priority, made warnings immediate, added reset/print actions and accessibility states, and tested the complete flow. The earlier project and AI-assisted development are disclosed; this release is not represented as an entirely new project.

Codex assisted with implementation, debugging, verification, documentation, and submission preparation. React, Vite, Tailwind, lucide-react, Base UI and shadcn UI are third-party dependencies/components, identified in package.json. Resource links point to HRSA, 211 and MedlinePlus; CareRoute is not affiliated with those services.

## Limits and next work

Resources and emergency numbers are US-focused. Care availability and individual fees must be confirmed with providers. No patient study, clinical validation, customer adoption, revenue, or outcome improvement is claimed. Next steps are user testing, accessibility review, professional review of copy, and broader language evaluation.

## Business proposal

The prototype is free and account-free. A possible later model is an institution-funded resource directory or embedding license for school clinics and nonprofits, keeping access free to individuals. This is a proposal, not an active paid service. Provider partnerships and evidence of demand must come before pricing, billing, or expansion.

## DSH healthcare entry - October 7

Live judge guide: https://careroute-access.vercel.app/about.html. Visit preparation now supports up to five user-authored questions in order, removal, stale-card invalidation and reset. The earlier core demo predates this addition. Questions remain in React memory, never localStorage or an API. Source and checks are included here.

## Question prioritization / STEMergent preparation
October 7 adds Up/Down controls that reorder user-authored questions and invalidate the old card. Guide: /stemergent.html. Event dates conflict; this release is not claimed as work during a future window.
