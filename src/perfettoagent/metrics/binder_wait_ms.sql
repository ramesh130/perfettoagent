-- @description: Time, in ms, the app's main thread spent waiting on synchronous binder calls to other processes, summed over the whole trace: the client-side duration of every synchronous transaction it made, as the Perfetto stdlib's android_binder_txns finds them. The app and its main thread are the same as the frame metrics': the process with the most window frames on the frame timeline, and the thread that draws them. Counted wherever the call was made, inside a frame or not. Oneway (async) calls do not wait and are left out, and so are the app's other threads. It cannot say why a reply was slow; android_binder_txns names the server process and, where traced, the AIDL method. NULL if the trace has no window frame (captured without the frametimeline data source) or no binder transaction at all (captured without the binder_driver atrace category).
-- @unit: ms
-- @requires_baseline: false
-- @no_data: the trace has no window frame on the frame timeline, so no app main thread, or no binder transaction by any process, so the binder_driver atrace category was likely off
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim. The app and
-- its main thread are chosen by the frame metrics' own query, copied verbatim down to
-- the `frames` CTE: change them together, and see jank_frames_pct.sql for why that app.
--
-- A transaction is a row of the stdlib's android_binder_txns; client_dur is the wall
-- time of the client's `binder transaction` slice, from the call to the reply. On the
-- jank fixtures it equals the sum of those slices on the main thread exactly.
-- ref: https://github.com/google/perfetto/blob/v58.2/src/trace_processor/perfetto_sql/stdlib/android/binder.sql
-- ref: https://perfetto.dev/docs/analysis/stdlib-docs#android-binder
--
-- The main thread only: that is where a wait stalls input and frames. The app's other
-- threads wait on binder for 9-20 s a capture on the jank scenario, against 0.1-1.1 s
-- on the main thread, and none of it holds up the thread that handles input and draws:
-- counted in, it would drown any change on the main thread. Synchronous only: a oneway
-- call returns at once. client_dur > 0 leaves out a call still waiting when the trace
-- ended.
--
-- Measured on all 15 jank captures (ADR-0013): 214.3-348.3 ms over 336-400 calls on the
-- six clean runs.
--
-- NULL rather than 0 when no process in the trace made a binder transaction: then the
-- binder_driver category was off. A trace with transactions, none of them the main
-- thread's, reads 0.
INCLUDE PERFETTO MODULE android.binder;
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
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_binder_txns) THEN NULL
    ELSE coalesce((
      SELECT sum(client_dur) FROM android_binder_txns
      WHERE is_sync AND client_dur > 0
        AND client_utid IN (SELECT ui_thread_utid FROM frames)
    ), 0) / 1e6
  END AS value
