# Eyas Design System — Themes

This folder contains **DESIGN.md** files that power the **Advanced Theme** selector in the Eyas Gradio UI.

## What is DESIGN.md?

DESIGN.md is a concept introduced by [Google Stitch](https://stitch.google.com).
A plain-text design system document that AI agents read to generate consistent,
visually accurate UI — no Figma exports, no JSON schemas, no special tooling.

| File | Who reads it | What it defines |
|------|-------------|-----------------|
| `AGENTS.md` | Coding agents | How to build the project |
| `DESIGN.md` | Design agents | How the project should look and feel |

Drop a `DESIGN.md` into your project root and any AI coding agent or Google
Stitch instantly understands how your UI should look. Markdown is the format
LLMs read best — nothing to parse or configure.

## Source

These files are sourced from the
**[awesome-design-md](https://github.com/VoltAgent/awesome-design-md)**
collection by VoltAgent — real design depth including analyzed color tokens,
typography rules, and layout patterns extracted from production websites.

> Built with real design depth — including analyzed patterns, tokens, and rules
> — for high-quality UI generation, not surface-level outputs.

## Themes

| Folder | Brand | Aesthetic |
|--------|-------|-----------|
| `voltagent/` | VoltAgent | Void-black canvas, emerald accent, terminal-native |
| `x.ai/` | xAI | Stark near-black, futuristic monochrome |
| `warp/` | Warp | Warm near-charcoal, understated cream CTA |
| `linear.app/` | Linear | Ultra-minimal near-black, lavender-blue accent |
| `sentry/` | Sentry | Deep purple midnight, electric lime accent |
| `stripe/` | Stripe | Navy ink, electric indigo, weight-300 elegance |
| `supabase/` | Supabase | Dark canvas, signature emerald-green CTA |
| `vercel/` | Vercel | Stark black, Geist precision, blue link accent |
| `cursor/` | Cursor | Warm cream editorial, Cursor Orange CTA |
| `runwayml/` | Runway | Cinematic full-bleed dark, zero-chrome interface |

## How these are used

The Eyas Gradio app reads these palettes at startup to power the
**Advanced Theme** dropdown in **Settings → Advanced Theme**.
Select a theme, click **Save advanced theme**, then restart the server.
