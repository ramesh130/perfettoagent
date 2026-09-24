-- @description: Native memory, in bytes, that heapprofd saw allocated and not freed by the end of the trace: allocations minus frees, summed over every sampled callstack of every profiled process (heapprofd profiles only the processes its trace config names). Native heaps only: ART's Java heap, when heapprofd samples it too, is left out. The values are heapprofd's sampled estimates, not exact counts. It cannot say which callstack leaked; heap_profile_allocation has one row per callstack and dump. NULL if the trace has no native heapprofd samples, which is the case for any trace captured without the android.heapprofd data source.
-- @unit: bytes
-- @requires_baseline: false
-- @no_data: the trace has no native heap profile: it was captured without the android.heapprofd data source
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim.
--
-- Unfreed is the sum of `size` over heap_profile_allocation: each row is one callstack's
-- allocations (positive) or frees (negative) since the previous dump, so the sum over
-- every row is what was still allocated at the last dump. It is the stdlib's own
-- "unreleased" (self_size in its heap profile summary tree), summed over every
-- callstack; that module builds the whole tree, which a total does not need.
-- ref: https://perfetto.dev/docs/data-sources/native-heap-profiler
-- ref: https://perfetto.dev/docs/analysis/sql-tables#heap_profile_allocation
-- ref: https://github.com/google/perfetto/blob/v58.2/src/trace_processor/perfetto_sql/stdlib/android/memory/heap_profile/summary_tree.sql
--
-- Every profiled process, not the frame metrics' app: a heapprofd capture already names
-- the processes it profiles, and it rarely has the frame timeline that choice needs.
-- Native only: `com.android.art` is heapprofd's name for the Java heap, which
-- heap_growth_objects_by_class measures from heap dumps instead.
--
-- No fixture has heapprofd data (ADR-0014), so the value path below is untested against
-- a real profile; the NULL path is tested on every fixture, in
-- tests/test_metrics_thread_memory.py. NULL rather than 0: with no
-- samples, nothing was measured, which is not the same as nothing unfreed.
SELECT
  CASE WHEN count(*) = 0 THEN NULL ELSE sum(size) END AS value
FROM heap_profile_allocation
WHERE heap_name IS NOT 'com.android.art'
