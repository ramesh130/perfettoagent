-- @description: Share of the app's UI frames, in percent, that SurfaceFlinger's frame timeline marks as App Deadline Missed: the app itself finished the frame too late. The frames are every frame of the app's own window (not its SurfaceView video layers) that has a timeline row and was presented before the trace ended; the app is the process with the most such frames. Jank the timeline blames on SurfaceFlinger, the display or buffer queueing (Buffer Stuffing, Prediction Error) is not counted. It says how many frames were late, not by how much or why. NULL if the trace has no such frame, which is the case when it was captured without the frametimeline data source.
-- @unit: percent
-- @requires_baseline: true
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim. The four
-- frame metrics (this file, frame_p95_ms.sql, frame_p99_ms.sql and
-- frame_ui_time_p95_ms.sql) share one query down to the `frames` CTE: change them
-- together. This file carries the argument, for all four, of which frames count.
--
-- Which frames. A frame is a row of the stdlib's android_frames_layers: one vsync of the
-- app's UI thread (Choreographer#doFrame, then DrawFrame on its RenderThread), matched
-- to SurfaceFlinger's actual timeline row for one layer. Every metric here reads the
-- timeline row: its dur runs from the frame's start to its present, and its jank_type is
-- SurfaceFlinger's verdict.
-- ref: https://perfetto.dev/docs/analysis/stdlib-docs#android-frames-timeline
-- ref: https://perfetto.dev/docs/data-sources/frametimeline
--
-- The window layer only. A process with video has SurfaceView layers (and a
-- "Background for … SurfaceView" layer each), whose buffers the decoder queues at the
-- content's rate. They get timeline rows for the same vsync ids as the window, so the
-- stdlib matches a frame to one row per layer. Counted in, they would count video
-- buffers as UI frames; and android_frames, which keeps one row per vsync, points at a
-- SurfaceView's row for most frames on the superPlayer captures (563 of 701), where app
-- jank read through it is 12.7% against 54.7% on the window's own rows (superPlayer
-- PR #392). So this reads android_frames_layers and drops every SurfaceView layer by
-- name.
--
-- Left out: a frame with no timeline row for the window (it never reached
-- SurfaceFlinger; 3-27 a capture in the fixtures), since it has neither a present nor a
-- verdict, and one still unpresented when the trace stopped (dur not positive). The
-- layers table can repeat a frame (one row per DrawFrame, and its fallback join is on
-- the vsync id alone), hence DISTINCT on the timeline row.
-- ref: https://github.com/google/perfetto/blob/v58.2/src/trace_processor/perfetto_sql/stdlib/android/frames/timeline.sql
--
-- The app is the process with the most window frames, ties broken by upid: a capture
-- drives one app, and the launcher or SystemUI drawing a frame or two during it
-- (2-3 frames on the superPlayer captures) must not be mixed in.
--
-- Jank is App Deadline Missed only: on the API 36 emulator 94-100% of frames carry some
-- jank_type, almost all Buffer Stuffing and Prediction Error, the same for every build
-- (ADR-0011). A frame whose jank_type lists several reasons counts if one of them is
-- the app's, hence GLOB rather than equality.
-- ref: https://perfetto.dev/docs/data-sources/frametimeline#janks
--
-- Checked against every frame's row, with the share taken in Python, and against
-- superPlayer devicelab's jank/sql/frames.sql by hand, on the fixtures in
-- tests/test_metrics_frames.py.
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
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
