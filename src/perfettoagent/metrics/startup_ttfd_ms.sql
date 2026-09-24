-- @description: Time to full display (TTFD) of the app's cold starts, in ms: the median (p50, nearest rank) over every cold start of the app in the trace. The app is the package with the most cold starts; warm and hot starts are left out. TTFD ends at the first frame after the app calls reportFullyDrawn, so it includes whatever the app waits for before that call, such as a network fetch. NULL if no cold start has a TTFD, which is the case when the app never calls reportFullyDrawn.
-- @unit: ms
-- @requires_baseline: true
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim. This file
-- and startup_ttid_ms.sql are the same query over a different column: change both, and
-- see startup_ttid_ms.sql for why the median, why cold starts only and how the app is
-- chosen.
--
-- TTFD is the stdlib's: from the start of the launch to the end of the first frame the
-- app's RenderThread draws after (or during) the first reportFullyDrawn on its main
-- thread. The platform's "Fully drawn" logcat line stops at the call itself, so it
-- reads up to about 200 ms shorter on the same start (ADR-0009).
-- ref: https://perfetto.dev/docs/analysis/stdlib-docs#android-startup-time_to_display
-- ref: https://developer.android.com/topic/performance/vitals/launch-time#retrieve-TTFD
--
-- Starts with no TTFD (no reportFullyDrawn found) are left out of the median, not
-- counted as 0.
--
-- Checked against every start's value, with the median taken in Python, on the
-- fixtures in tests/test_metrics_startup.py.
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
