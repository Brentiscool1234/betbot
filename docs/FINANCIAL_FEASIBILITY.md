# Financial feasibility — 2026-10-13

## Approved low-cost proof of concept

Owner requested a total hosting + odds budget of 20/month; assume EUR pending
currency confirmation. Use The Odds API free tier (500 credits/month) and a VPS
with an all-in hosting/backup/tax quote below EUR 20; target EUR 5–10. No paid
odds renewal, statistics purchase or host provisioning is authorized by this
budget. Current account billing/renewal must be checked by the owner: free-tier
collection does not itself cancel an existing subscription. Existing historical
archives remain reusable without API calls; do not run new historical downloads
on the free plan. Historical access may be lost after downgrading.

Pilot cadence: every 6h normally, hourly within 6h of nearest kickoff. Cap at
20 credits/day and 400/calendar month, preserving 100 provider credits. This
is a sparse collection pilot; exact closing quotes and full horizon coverage
are not promised. Other clients using this API key consume the same allowance.
Calendar limits and provider renewal periods can differ; quota protection remains
in place. Check provider pricing/eligibility before downgrading.

The EUR 20 pilot tests ingestion, timestamp integrity, uptime and operating cost.
It cannot establish profitability or complete result-based model research without
a suitable licensed results/statistics source. The previous paid-plan estimate
below is comparison context, not the chosen pilot cost.


Recommendation: a bounded research pilot, one small VPS, UK region, EPL 1X2 only.
Keep existing API subscription; do not add premium statistics, ML infrastructure
or a dashboard until source coverage and data integrity justify the expense.

## Costs and uncertainty

The Odds API public pricing at https://the-odds-api.com/ lists a 20,000-credit plan
at USD 30/month and a 100,000-credit plan at USD 59/month. Current account billing,
renewal dates, taxes and any discounts are unknown. Available credits do not
prove which subscription is billed. No purchase or plan change was made.
The free tier lists 500 credits/month; reliable historical access needs a paid
plan. Reconfirm checkout terms before choosing a subscription.

Allow EUR 5–10/month as an estimated budget for a small Ubuntu VPS, including a
small backup allowance; this is a planning assumption, not a verified host quote.
Storage/archive growth, backup charges, VAT and exchange rates vary. Hosting is
not provisioned. A licensed results/statistics source is REQUIRED and currently
unpriced: total project cost cannot yet be declared feasible.

For comparison, a paid historical-access setup would cost USD 30/month plus
EUR 5–10 hosting. Keep currencies separate; do not silently sum them. Engineering
time and future statistics licensing are additional costs. An illustrative
approval ceiling for the pilot would be EUR 50-equivalent/month TOTAL, but no
such budget has been confirmed by the owner. Check actual billing and a statistics
quote against the chosen ceiling before buying anything.

## Credit budget

A UK/1X2 request cost 1 credit in the live verification; each sampled historical
request cost 10. Twelve historical requests used 120 credits; one initial live
request used 1. Cached historical reruns incur no new API charge once complete.
The historical command has a default bound of 20 requests / about 200 credits.
Additional markets/regions and changed provider billing multiply costs.

Prospective defaults: at most 20 reserved credits per UTC day and 400 per UTC
month, retaining a 100-credit provider reserve. Counters are persisted before
requests; failures retain their reservation. Returned quota headers increase
accounted usage if actual cost is larger. A provider unexpectedly charging more
than the reservation can cause a one-request overshoot; this is a credit guard,
not a guaranteed currency cap. No automatic purchases/upgrades/top-ups occur.
Preserve budget.json on migration/restarts. Separate directories have separate
ledgers; use exactly one collector directory on the chosen host.

| Collection profile | Approximate credits/30 days |
| --- | ---: |
| Every 6 hours | 120 |
| Every hour | 720 |
| Every 15 minutes | 2,880 |
| Every 5 minutes | 8,640 |
| Implemented adaptive polling | Fixture-dependent, capped at 400 accounted credits |

The watcher checks every minute but only makes a paid request when due. Pilot mode uses 6h normally and 1h within 6h of nearest kickoff. Research mode
retains the former faster cadence, but is not the default for this budget.
The day/month cap may deliberately stop a busy-day collection; health checks
expose lost coverage. Do not describe capped coverage as complete. Tune limits
only after a measured week of credit usage and fixture/quote coverage.

## Economic decision gates

1. Complete licensing and publication audit within the agreed total monthly cap.
2. Measure a week of uptime, missing horizons, actual credits and archive growth.
3. Run chronological market-baseline research only after Phase 1 acceptance.
4. Freeze a candidate and collect 8–12 weeks of paper evidence.
5. Stop or redesign if calibration or incremental market information fails.

There is no established return, probability model or financial edge. The system
is paper/research only. An operating budget does not establish profitability.
For illustration only: if monthly costs were EUR 50, break-even hypothetical
turnover would be EUR 5,000 at a TRUE 1% net advantage, or EUR 2,500 at 2%, before
capital risk, taxes and other costs. Those advantages are unproven; these figures
are sensitivity examples, not a recommendation or projected return.
