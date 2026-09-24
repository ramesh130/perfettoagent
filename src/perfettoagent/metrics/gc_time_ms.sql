-- @description: Wall time, in ms, the app's garbage collector spent collecting over the whole trace: the sum of the durations of every ART collection in the app's process (on its HeapTaskDaemon), as the Perfetto stdlib's android_garbage_collection_events finds them. The app is the same as the frame metrics': the process with the most window frames on the frame timeline. A concurrent collection runs beside the app's threads, so this is how hard the collector worked, which grows with allocation; it is not the time the app was paused, and it cannot say what was allocated. NULL if the trace has no window frame (captured without the frametimeline data source) or no collection by any process (captured without the dalvik atrace category).
-- @unit: ms
-- @requires_baseline: false
-- @no_data: the trace has no window frame on the frame timeline, so no app, or no garbage collection by any process, so the dalvik atrace category was likely off
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim. The app is
-- chosen by the frame metrics' own query, copied verbatim down to the `frames` CTE:
-- change them together, and see jank_frames_pct.sql for why that app.
--
-- A collection is a row of the stdlib's android_garbage_collection_events: a top-level
-- `*concurrent*GC` slice (ART's `Background young concurrent mark compact GC` and
-- kin), with its CompactionPhase when that ran outside it. gc_dur is its wall time,
-- to the end of the trace for one still running then.
-- ref: https://github.com/google/perfetto/blob/v58.2/src/trace_processor/perfetto_sql/stdlib/android/garbage_collection.sql
-- ref: https://perfetto.dev/docs/analysis/stdlib-docs#android-garbage_collection
--
-- Not the `GC: Wait For Completion …` slices: those are other threads waiting for one
-- of these collections, the same time counted again. A main thread that waits for one
-- outside a frame is in main_thread_blocked_ms.
--
-- The app's process only: the system server, Bluetooth and the phone process collect
-- too (17 of the 24 collections in the clean baseline fixture are theirs), and none of
-- that is the app's code.
--
-- Measured on all 15 jank captures (ADR-0013): 6-8 collections and 172.0-428.5 ms on
-- the six clean runs, 134-149 collections and 9484.5-11044.5 ms on the three that
-- allocate a million boxed floats in each scrolled frame.
--
-- NULL rather than 0 when no process in the trace collected at all: then the `dalvik`
-- category was off and nothing can be said. A trace with collections, none of them the
-- app's, reads 0.
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
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
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_garbage_collection_events) THEN NULL
    ELSE coalesce((
      SELECT sum(gc_dur) FROM android_garbage_collection_events
      WHERE upid = (SELECT upid FROM app)
    ), 0) / 1e6
  END AS value
