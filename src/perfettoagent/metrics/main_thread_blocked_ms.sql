-- @description: Time, in ms, the app's main thread spent blocked in the middle of work other than drawing a frame: not running and not waiting for a CPU (asleep, or in uninterruptible wait such as disk I/O) while inside one of its top-level traced slices other than Choreographer#doFrame, such as an input event, a message handler, a binder call or a lock wait. Summed over the whole trace. The app and its main thread are the same as the frame metrics': the process with the most window frames on the frame timeline, and the thread that draws them. It cannot say what the thread waited for (a sleep, a lock and a binder reply all look alike), and it leaves out blocking inside a doFrame, which frame_ui_time_p95_ms measures, and blocking in untraced code, which looks like an idle main thread. NULL if the trace has no window frame (captured without the frametimeline data source) or no scheduler data for the main thread.
-- @unit: ms
-- @requires_baseline: false
-- @no_data: the trace has no window frame on the frame timeline, so no app main thread, or no scheduler (thread_state) data for that thread
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim. The app and
-- its main thread are chosen by the frame metrics' own query, copied verbatim down to
-- the `frames` CTE: change them together, and see jank_frames_pct.sql for why that app.
-- Its UI thread is the main thread for any app that draws its window from Java.
--
-- Blocked is any thread_state that is neither Running nor runnable (R, R+): S (asleep:
-- Thread.sleep, a lock, a binder reply, a condition variable), D (uninterruptible:
-- usually I/O) and the kernel's rarer states. Runnable is left out because it is the
-- CPU being busy, not the thread waiting on something.
-- ref: https://perfetto.dev/docs/data-sources/cpu-scheduling#decoding-code-end_state-code-
--
-- Only inside the thread's top-level slices: an idle main thread also sleeps, in its
-- Looper waiting for the next message, and that is most of any trace (41.7 s of the
-- 49.5 s the main thread slept on the clean baseline fixture). A sleep inside a slice
-- is a sleep in the middle of traced work. Counted as the overlap with each slice, so
-- a state that began before the slice counts from the slice's start.
--
-- Not inside Choreographer#doFrame. On the jank captures (ADR-0013) the main thread
-- sleeps 7.7-9.9 s inside doFrames on a clean build: mostly postAndWait, handing the
-- frame to its RenderThread, and Compose:onForgotten as rows scroll away. That spread,
-- 2.2 s, is three times the 706 ms one planted change adds, so a metric that counted
-- it could not see such a stall. Blocking inside a frame is already in the
-- frame's own duration, which frame_ui_time_p95_ms measures, and binder_wait_ms counts
-- the main thread's binder waits wherever they are. A tap's click handler runs outside
-- doFrame: Android batches only move events into the next frame, and delivers a
-- touch's down and up at once, as their own deliverInputEvent (all 6 taps a capture
-- are top-level slices on the jank captures).
-- ref: https://developer.android.com/reference/android/view/MotionEvent#batching
--
-- Measured on all 15 jank captures (ADR-0013): 9.3-38.9 ms on the six clean runs,
-- 731.5-748.2 ms on the three runs of the plant this metric is expected to catch.
--
-- The overlap is a plain join, not the stdlib's interval intersection: that is the
-- private macro _interval_intersect!, and both sides here are already disjoint
-- intervals of one thread, so the sum of pairwise overlaps is exact.
--
-- Checked against every state and top-level slice of the main thread (found by its
-- tid), with the overlap taken in Python, in tests/test_metrics_thread_memory.py.
--
-- NULL rather than 0 when the main thread has no thread_state at all: without the
-- sched_switch events nothing here can tell blocked from running.
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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM frames
  ),
  work AS (
    SELECT s.ts, s.dur
    FROM slice AS s
    JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.dur > 0
      AND s.name NOT GLOB 'Choreographer#doFrame*'
  ),
  blocked AS (
    SELECT ts, dur
    FROM thread_state
    WHERE utid IN (SELECT utid FROM main_thread)
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')
  )
SELECT
  CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM thread_state WHERE utid IN (SELECT utid FROM main_thread)
    ) THEN NULL
    ELSE coalesce((
      SELECT sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts))
      FROM blocked AS b
      JOIN work AS w ON b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur
    ), 0) / 1e6
  END AS value
