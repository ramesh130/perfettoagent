-- @description: 95th percentile (nearest rank) of the app's UI time per frame, in ms: how long the thread that draws its window spent in each Choreographer#doFrame (input, animation, measure, layout and recording the draw), over every doFrame of that thread in the trace. The app is the same as frame_p95_ms's, the process with the most window frames on the frame timeline. It leaves out the RenderThread and SurfaceFlinger, so it moves with work the app does on its UI thread in every frame and not with display-pipeline noise; it cannot say which part of doFrame was slow, or whether a frame was presented late. NULL if the trace has no window frame, which is the case when it was captured without the frametimeline data source.
-- @unit: ms
-- @requires_baseline: true
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim. This file
-- shares its query with the other frame and thread metrics down to the `frames` CTE,
-- listed in jank_frames_pct.sql: change them
-- together, and see jank_frames_pct.sql for which frames and app are chosen.
--
-- UI time is the stdlib's: a Choreographer#doFrame slice's duration, as
-- android_frames_ui_time defines it, over the doFrames the stdlib parses a vsync id
-- from (the "resynced" ones are left out). That table has no thread or process column,
-- so its source, android_frames_choreographer_do_frame, is read here instead.
-- ref: https://github.com/google/perfetto/blob/v58.2/src/trace_processor/perfetto_sql/stdlib/android/frames/timeline.sql
-- ref: https://perfetto.dev/docs/analysis/stdlib-docs#android-frames-timeline
--
-- The UI thread is the one whose doFrames drew the app's window frames. Other threads
-- can run a Choreographer too: superPlayer's player pool does, 115-122 doFrames of
-- under 3 ms a capture, which would pull the percentile down if counted.
--
-- Every doFrame of that thread, not only those matched to a window frame: a vsync
-- callback that drew nothing new still ran on the UI thread, and per-frame UI-thread
-- work is what this measures. Measured both ways on the superPlayer jank captures
-- (ADR-0011), the planted runs clear every clean run by at least 3.0 times the clean
-- spread this way, and by 1.5 times over window frames only.
--
-- Why this metric exists beside frame_p95_ms (ADR-0011): on the emulator a frame's
-- timeline duration is mostly SurfaceFlinger queueing, which varies between captures
-- of one build and drowns a per-frame regression in the app. frame_p95_ms separates
-- neither per-frame plant from its own clean spread; this one separates both.
--
-- Nearest rank, the value at rank ceil(0.95 n), so the number is one real doFrame's.
-- ref: https://en.wikipedia.org/wiki/Percentile#The_nearest-rank_method
--
-- Checked against every doFrame slice on the app's UI thread, with the percentile
-- taken in Python, on the fixtures in tests/test_metrics_frames.py.
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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
