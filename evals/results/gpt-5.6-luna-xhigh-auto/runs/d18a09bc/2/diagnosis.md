# Inconclusive

- **Metric:** `frame_ui_time_p95_ms` +3.54 ms (8.47 → 12 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 0 dropped; 12 of 12 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 8.47 | 12 | +3.54 |

Measured by:

```sql
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
```

## Claims

### c1. The selected app UI-frame p95 increased from 8.4665 ms in baseline to 12.004708 ms in current.

The `baseline` trace: 1 row.

```sql
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
```

The `current` trace: 1 row.

```sql
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
```

### c2. The localized work is on com.example.jetnews's main thread. AndroidOwner:measureAndLayout had a maximum of 2.219958 ms in baseline versus 4.420958 ms in current, while Record View#draw() had a maximum of 3.21575 ms versus 5.304417 ms.

The `baseline` trace: 4 rows.

```sql
SELECT CASE WHEN s.name GLOB 'ViewPostImeInputStage*' THEN 'ViewPostImeInputStage' ELSE s.name END AS slice_group,
  count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id
JOIN thread th ON th.utid=tt.utid
JOIN process p ON p.upid=th.upid
WHERE p.name='com.example.jetnews'
  AND (s.name GLOB 'ViewPostImeInputStage*' OR s.name IN ('postAndWait','AndroidOwner:measureAndLayout','Record View#draw()'))
GROUP BY slice_group
ORDER BY slice_group
```

The `current` trace: 4 rows.

```sql
SELECT CASE WHEN s.name GLOB 'ViewPostImeInputStage*' THEN 'ViewPostImeInputStage' ELSE s.name END AS slice_group,
  count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id
JOIN thread th ON th.utid=tt.utid
JOIN process p ON p.upid=th.upid
WHERE p.name='com.example.jetnews'
  AND (s.name GLOB 'ViewPostImeInputStage*' OR s.name IN ('postAndWait','AndroidOwner:measureAndLayout','Record View#draw()'))
GROUP BY slice_group
ORDER BY slice_group
```

### c3. The current tail also contains substantially larger wait and input-stage slices: postAndWait reached 14.897167 ms versus 8.071792 ms in baseline, and ViewPostImeInputStage reached 18.2035 ms versus 3.87625 ms.

The `baseline` trace: 4 rows.

```sql
SELECT CASE WHEN s.name GLOB 'ViewPostImeInputStage*' THEN 'ViewPostImeInputStage' ELSE s.name END AS slice_group,
  count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id
JOIN thread th ON th.utid=tt.utid
JOIN process p ON p.upid=th.upid
WHERE p.name='com.example.jetnews'
  AND (s.name GLOB 'ViewPostImeInputStage*' OR s.name IN ('postAndWait','AndroidOwner:measureAndLayout','Record View#draw()'))
GROUP BY slice_group
ORDER BY slice_group
```

The `current` trace: 4 rows.

```sql
SELECT CASE WHEN s.name GLOB 'ViewPostImeInputStage*' THEN 'ViewPostImeInputStage' ELSE s.name END AS slice_group,
  count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id
JOIN thread th ON th.utid=tt.utid
JOIN process p ON p.upid=th.upid
WHERE p.name='com.example.jetnews'
  AND (s.name GLOB 'ViewPostImeInputStage*' OR s.name IN ('postAndWait','AndroidOwner:measureAndLayout','Record View#draw()'))
GROUP BY slice_group
ORDER BY slice_group
```

### c4. The range contains relevant UI-geometry edits: commit 6213c5a80f4b44de4b2a21e92bf6ef5af1b4f83c changes the PostCards dialog button, and commit ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1 changes SelectTopicButton sizing.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
6213c5a80f4b44de4b2a21e92bf6ef5af1b4f83c
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

### c5. The traces establish a frame-tail regression, but the localized increase is mixed with wait and input-stage outliers rather than a component-specific trace row. Therefore neither range edit can be attributed as the cause from these captures.

The `baseline` trace: 4 rows.

```sql
SELECT CASE WHEN s.name GLOB 'ViewPostImeInputStage*' THEN 'ViewPostImeInputStage' ELSE s.name END AS slice_group,
  count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id
JOIN thread th ON th.utid=tt.utid
JOIN process p ON p.upid=th.upid
WHERE p.name='com.example.jetnews'
  AND (s.name GLOB 'ViewPostImeInputStage*' OR s.name IN ('postAndWait','AndroidOwner:measureAndLayout','Record View#draw()'))
GROUP BY slice_group
ORDER BY slice_group
```

The `current` trace: 4 rows.

```sql
SELECT CASE WHEN s.name GLOB 'ViewPostImeInputStage*' THEN 'ViewPostImeInputStage' ELSE s.name END AS slice_group,
  count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id
JOIN thread th ON th.utid=tt.utid
JOIN process p ON p.upid=th.upid
WHERE p.name='com.example.jetnews'
  AND (s.name GLOB 'ViewPostImeInputStage*' OR s.name IN ('postAndWait','AndroidOwner:measureAndLayout','Record View#draw()'))
GROUP BY slice_group
ORDER BY slice_group
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
6213c5a80f4b44de4b2a21e92bf6ef5af1b4f83c
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available on each side, so p95 and frame-tail differences can be affected by run-to-run scheduling noise.
- The current capture is from an emulator debug build; this is not a release-device comparison.
- The traces do not provide a component-specific app stack attribution for the changed UI code.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 93 tool calls, $0.0710, 266 s.
Tokens: 66 input, 940,872 cache read, 85,639 cache write, 25,653 output.
