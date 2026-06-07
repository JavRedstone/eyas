# AI & CCTV: How theft-detection systems work — Practical overview

This note explains common approaches, realistic capabilities, limitations, and best practices for using AI to detect theft or suspicious activity from CCTV. It emphasizes how most systems generate alerts (leads) for human review rather than making definitive accusations.

## Summary
- With only CCTV, systems can narrow hours of footage to candidate events (concealment, unusual behavior, exit without visible checkout) but rarely prove theft.
- Reliable detection typically combines multiple signals: POS records, weight sensors, inventory data, and many cameras.
- Production systems prioritize low false-positive rates and human review.

## Common signals and approaches

1. Exception-based checkout monitoring
- Compare items seen at checkout (camera, weight, self-checkout sensors) with scanned items and transaction records.
- Typical alerts: skipped scan, barcode switching, bagging-area weight mismatch.

2. Computer-vision verification at checkout
- Cameras observe the scanning area to verify items presented match scans.
- Useful at self-checkout and manned lanes where cameras see the handoff.

3. Loss-prevention analytics (multi-signal)
- Fuse CCTV, POS, inventory shrinkage reports, and employee notes to find patterns (hot aisles, repeated suspicious transactions).

4. Exit monitoring and virtual cart approaches
- Track items taken from shelves and compare against receipts when possible.
- Amazon Go–style systems maintain a virtual cart using dense camera coverage and sensors; this requires extensive infrastructure.

5. CCTV-only heuristics
- Person tracking across cameras to establish trajectories.
- Object-interaction detection: picking, concealing, placing in bag/pocket.
- Dwell-time and loitering detection in high-risk areas.
- Exit without visible checkout or leaving with concealed item.

## What CCTV-only systems can and cannot do

Can reasonably do (with caveats):
- Detect unusual behavior patterns (loitering, concealment gestures).
- Flag events where an item appears to be removed from a shelf and a person later leaves without a visible checkout.
- Produce short clips and timestamps to speed human review.

Cannot reliably do alone:
- Prove the exact SKU taken with high confidence under real-world occlusion and product similarity.
- Know whether an item was paid for without POS integration.
- Distinguish a returned or transferred item from a stolen one in many contexts.

Accuracy depends on:
- Camera placement, resolution, and frame rate
- Lighting and occlusion (bags, clothing, other shoppers)
- Product size, packaging, and visual similarity
- Density of store traffic and camera coverage

## Typical production workflow
1. AI analyses generate a suspicion score or discrete alerts.
2. Alerts are triaged and displayed with short clips and metadata (time, location, involved person).
3. A loss-prevention analyst reviews the clips and decides whether to escalate.
4. If needed, staff intervene following store policy.

Most retailers avoid automatic interventions based on vision-only alerts due to legal and reputational risks.

## Best practices for minimizing false positives
- Combine vision with transaction and sensor data when possible (POS logs, bagging scales, RFID).
- Use conservative thresholds for automatic alerts.
- Prioritize human-in-the-loop review for escalation.
- Log and audit alerts and reviewer actions for accountability.

## Privacy, ethics, and legal considerations
- Check local laws for video surveillance, recording consent, and automated decisionmaking.
- Avoid biometric identification (face recognition) unless compliant and necessary — that raises legal and ethical issues.
- Minimize retention of personally identifying data; anonymize where possible.
- Use alerts as leads, not proof. Ensure processes protect customers' rights and staff safety.

## How multi-camera / cashierless systems differ
- Dense multi-camera systems and weight/RFID sensors allow building a "virtual cart" and achieve much higher accuracy.
- These systems require significant engineering and hardware coverage; they are practical for large-scale cashierless stores but costly for small shops.

## Practical guidance for small stores / prototypes
- If you only have CCTV, focus on generating high-quality clips and concise metadata (time, zone, person trajectory) for human review.
- Use simple heuristics: zone-based shelf removal + subsequent exit without checkout → flag.
- Integrate any available POS or receipt data to dramatically improve precision.
- Keep UI focused: provide short clips, context (pre/post frames), and a clear suggested action for staff.

## Final note
AI can make loss-prevention teams more efficient by surfacing candidate events, but it rarely, by itself, determines guilt. The right approach combines multiple signals, conservative thresholds, and human oversight.