-- @description: Reachable Java objects in the last Java heap dump of each trace. The headline is all reachable objects; the breakdown is per class, ranked by growth from baseline to current.
-- @unit: objects
-- @requires_baseline: true
-- @key: class
--
-- Everything above the first line that is not a comment is metadata (the @fields) or
-- notes for whoever edits this file. What follows it is sql_used, verbatim.
--
-- Reachable only: an object no GC root reaches is garbage the collector has not yet
-- freed, and how much of it a dump holds depends on when the last GC ran, not on the
-- code under test. Trace processor marks reachability by walking from the roots, and the
-- stdlib aggregation counts it per class, so nothing here re-derives that walk.
-- ref: https://perfetto.dev/docs/analysis/stdlib-docs#android-memory-heap_graph-heap_graph_class_aggregation
-- ref: https://perfetto.dev/docs/data-sources/java-heap-profiler
--
-- The last dump: a trace can hold several (one per trigger, or one per process). The
-- last one is the state the trace ended in, which is what a baseline is compared at.
-- With dumps of several processes, that is the one process dumped last; the traces
-- this compares (one app, one dump each, as devicelab captures them) hold one.
--
-- Grouped by name, not class id: a class loaded by two class loaders is two ids with one
-- name, and splitting it would show one class twice.
--
-- Checked against the raw tables (heap_graph_object.reachable joined to
-- heap_graph_class) on the fixture pair in tests/test_metrics.py.
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key
