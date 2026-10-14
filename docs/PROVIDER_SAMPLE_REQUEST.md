# Historical EPL sample request — 2026-10-13

Status: researched public coverage/pricing and prepared this request. No email or
support message has been sent; no subscription/trial was activated.

## Public findings

Official plans: https://www.sportmonks.com/football-api/plans-pricing/
Starter is advertised from EUR 29/month (EUR 24/month with annual billing), with
five selected leagues. A 14-day paid-plan trial requires subscription and converts
to billing unless cancelled. Prices exclude VAT under the provider's terms.
Historical data older than three seasons is advertised as a separate one-time
add-on from EUR 29; exact entitlement to the 2024/25 sample must be confirmed.
Our required season is 2024/25, not an automatic reason to buy that add-on.
xG is separately packaged; optional for the initial goals-based research.

Terms: https://www.sportmonks.com/terms-of-service/
Public terms allow building applications and prohibit unapproved raw-data resale.
Confirm our private immutable retention/model-research use in the written reply,
including after subscription cancellation. No permission has been inferred for
training with a particular account's data or for republishing raw exports.

Demo: https://docs.sportmonks.com/v3/api/demo-response-files
An EPL demo response for 2025/26 fixture 19427552 is documented. This is an API
schema example, not a historical publication audit or a 2024 sample. Public docs
mention statistics, lineups and events but do not establish versioned historical
publication times. We have not obtained a token-gated licensed 2024 sample.

## Ready-to-send request

To: Sportmonks support, via https://www.sportmonks.com/contact-support/
Subject: EPL 2024/25 research sample, publication timestamps and small-project pricing

Hello,

We are building a private, paper-only EPL probability research proof of concept.
We already have timestamped 1X2 bookmaker snapshots for 100 EPL fixtures in the
2024/25 season. Before subscribing, could you provide a small licensed sample
(5–10 matches) with:

- Stable fixture/team IDs, UTC kickoff, match status and final home/away scores.
- Per-team shots and shots on target, with corners/cards if included; xG optional.
- Source publication/update times and revision history, if available.
- Clear distinction between original historical observations and latest corrected
  values. Does the API permit reconstructing information available at an earlier
  prediction cutoff, or does it only return today's latest version?
- Confirmation that we may store immutable raw responses indefinitely and use
  them for private statistical/model research, including after cancellation.
- Exact monthly total (and any one-time historical fee) for EPL only/lowest plan,
  VAT treatment, sample/trial access and cancellation conditions.

Our initial goal is data integrity and low operating cost, not live wagering.
If historical publication/revision evidence is unavailable, please say so; we
would instead evaluate prospective collection. We can provide our fixture list
privately for matching once sample access and rights are agreed.

Thank you.

## Sample acceptance checklist

Verify licence and costs first; archive response plus checksum/receipt time.
Map provider IDs to Odds API IDs by reviewed teams and UTC kickoff. Reject
ambiguous mappings and unexplained reschedules. Missing statistics remain missing.
Treat retrospective values as observed-only unless historical publication evidence
is supplied; never infer publication at kickoff. Latest final scores can serve as
outcome labels, but cannot be fed into historical inputs before actual availability.
Do not use season-end aggregates as earlier-match features. Confirm coverage and
revisions, then consider 100-match import. Phase 1 remains gated until acceptance.

## No-additional-subscription fallback

Existing Odds API scores endpoint supports recent completed EPL results, not
shots/xG/lineups or 2024 historical results. Six-hour polling with daysFrom=3 costs
2 credits/call: approximately 240 credits per 30 days. Receipt time is availability;
provider last_update is an effective/source update, not permission to backdate.
The current point-in-time store can retain these labels and support future
rolling-goals/points research after enough observed history accumulates. It does
not by itself complete the historical statistics requirement. Monitor outages;
gaps longer than three days may be unrecoverable from this endpoint.
