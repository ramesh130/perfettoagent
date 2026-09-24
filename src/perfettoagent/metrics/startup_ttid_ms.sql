-- @description: Time to initial display (TTID) of the app's cold starts, in ms: the median (p50, nearest rank) over every cold start of the app in the trace. The app is the package with the most cold starts; warm and hot starts are left out. NULL if the trace has no cold start with a TTID, which is the case when it was captured without the frametimeline data source.
-- @unit: ms
-- @requires_baseline: true
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim. This file
-- and startup_ttfd_ms.sql are the same query over a different column: change both.
--
-- TTID is the stdlib's: from the start of the launch to the end of the first frame the
-- app's RenderThread draws after it. ADR-0009 records that android_startups and this
-- table are reliable on API 36 emulator traces (Q4): 160 of 160 cold starts found, dur
-- within 1.1 ms of `am start -W` TotalTime, TTID within 26 ms of the platform's own
-- "Displayed" line.
-- ref: https://perfetto.dev/docs/analysis/stdlib-docs#android-startup-startups
-- ref: https://perfetto.dev/docs/analysis/stdlib-docs#android-startup-time_to_display
-- ref: https://developer.android.com/topic/performance/vitals/launch-time#time-initial
--
-- One number from many starts: a devicelab startup trace holds 20 cold starts. The
-- median, because the tail drifts: over one hour of clean runs the per-run p95 moved
-- from 456 to 813 ms while the p50 stayed within 105 ms (ADR-0009). Nearest rank, the
-- value at rank ceil(n/2), so the number is one real start's TTID, not an average of two.
-- ref: https://en.wikipedia.org/wiki/Percentile#The_nearest-rank_method
--
-- Cold starts only: a warm or hot start skips process creation and Application.onCreate,
-- so mixing them in would make the median depend on the mix, not on the code.
--
-- The app is the package with the most cold starts, ties broken by name: the traces
-- this compares launch one app over and over, and anything else started during the
-- capture (a launcher, a system app) must not be mixed into its distribution.
--
-- Starts with no TTID (no frame found) are left out of the median, not counted as 0.
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_initial_display AS ns
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
