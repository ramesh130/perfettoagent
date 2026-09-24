-- @description: 99th percentile (nearest rank) of how long the app's UI frames took, in ms, from the frame's start to its present on screen, per SurfaceFlinger's frame timeline. The frames are every frame of the app's own window (not its SurfaceView video layers) that has a timeline row and was presented before the trace ended; the app is the process with the most such frames. The time includes the app's UI thread and RenderThread and any wait in SurfaceFlinger's queue, so it cannot say which of them was slow. With a few hundred frames it is set by the slowest handful, so it moves between captures of the same build more than frame_p95_ms does. NULL if the trace has no such frame, which is the case when it was captured without the frametimeline data source.
-- @unit: ms
-- @requires_baseline: true
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim. This file
-- and frame_p95_ms.sql are the same query at a different rank: change both, and see
-- jank_frames_pct.sql for which frames are counted and why.
--
-- Nearest rank, the value at rank ceil(0.99 n), so the number is one real frame's
-- duration. On a 400-800 frame capture that is the 5th to 8th slowest frame.
-- ref: https://en.wikipedia.org/wiki/Percentile#The_nearest-rank_method
--
-- Checked against every frame's duration, with the percentile taken in Python, on the
-- fixtures in tests/test_metrics_frames.py.
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
