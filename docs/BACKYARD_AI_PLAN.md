# Build Small Hackathon Plan

This plan is optimized for a Backyard AI submission, but it also works as a filter for deciding whether to switch to the whimsical track. The main idea is to ground the project in one real operator, one repeated failure loop, and one transformation the model can perform reliably.

## Phase 1: Lock the real-world target

Spend 1 to 2 days identifying one real operator, ideally your partner's parent or another person you can observe directly. Do not design the app yet.

Extract the following:
- exact business type, such as bakery, salon, convenience store, or tutoring
- where orders or messages come from, such as WhatsApp, Instagram, phone, or in-person notes
- what is written versus what is remembered
- which mistakes happen repeatedly
- what costs time or money every week

Output for this phase:
- a 5 to 10 bullet workflow map of reality, not ideas

If you cannot get this, stop and switch targets. Everything else depends on it.

## Phase 2: Find one high-frequency failure loop

Do not try to solve multiple problems. Isolate a single broken loop.

Good loops look like:
- ambiguous customer requests leading to misinterpreted orders
- informal notes leading to forgotten commitments
- repeated pricing questions leading to inconsistent responses
- scheduling requests leading to unclear availability handling
- inventory mentions that are not tracked reliably

Selection rule:
- most frequent, ideally daily
- least structured today
- easiest to demonstrate in chat logs

Reject everything else.

## Phase 3: Define a transform, not assistant product

Do not frame the project as an AI assistant.

Aim for this pattern:
- messy human text in
- structured action plus clarification out

Valid transformations include:
- message to booking proposal plus clarification question
- conversation to order summary plus missing-info detection
- notes to structured inventory reorder list
- chat to commitment log plus follow-up list

Key constraint:
- the model must do interpretation, not conversation

## Phase 4: Design a minimal agent loop

Keep the system small and direct.

Typical structure:
1. input message stream, real or copied
2. small LLM classifies intent
3. extract entities such as time, item, price, and urgency
4. detect ambiguity
5. deterministic formatter turns the result into structured UI blocks
6. optional second LLM pass generates a suggested reply

Keep tools minimal, ideally zero to two.

## Phase 5: Build a real data strategy

Judging is much stronger when the project is grounded in real traces, not synthetic prompts.

Minimum viable dataset:
- 20 to 50 real messages from the operator
- anonymized if needed
- used in the demo

Better version:
- shadow mode during real work for 2 to 5 days
- log the input message
- log the model interpretation
- log the human response

This becomes evidence of use.

## Phase 6: Build the Gradio app around the workflow

Do not build a chatbot UI.

Build something like:
- inbox view for incoming messages
- structured interpretation panel
- suggested reply panel
- action items, schedule, or inventory updates

Optional additions:
- confidence indicators
- ambiguity flags such as missing price or unclear time

This is the easiest path to the Off-Brand bonus.

## Phase 7: Choose the model with the hackathon constraints in mind

Use a small LLM, ideally in the 7B to 14B range.

Prefer a local runtime if possible, especially llama.cpp if you want bonus eligibility.

Do not optimize for broad capability. Optimize for correctness on narrow domain patterns.

## Phase 8: Design the demo around proof, not explanation

The demo should show the pain and the fix.

Recommended flow:
1. show real messy input
2. show current manual handling
3. run the system
4. show structured output
5. show time saved or error prevented

Avoid architecture slides and generic UI walkthroughs.

## Phase 9: Add bonuses only after the core works

Once the main workflow is solid, layer in optional bonuses if they do not distract from the product.

- Off the Grid: run locally
- Llama Champion: use llama.cpp
- Sharing is Caring: log traces
- Field Notes: write a short report
- Off-Brand: customize the workflow UI

Do not pursue bonuses before the core loop is stable.

## Phase 10: Run the final evaluation check

Before submission, verify the following:
- Can a stranger understand the problem in 5 seconds?
- Does it clearly match one real person's job?
- Is there real message data?
- Does the system remove one specific daily annoyance?
- Can the project be described in one sentence without sounding generic?

If any answer is no, it is not ready.

## Compressed strategy
1. Find a real operator
2. Extract one real communication failure loop
3. Build a single transformation system, not an assistant
4. Use a small LLM for interpretation
5. Ground the project in real messages
6. Build a workflow UI, not a chatbot
7. Demonstrate the result with real data