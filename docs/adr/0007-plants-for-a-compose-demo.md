# Adapt two plants to the superPlayer demo, which is Jetpack Compose

The roadmap's plants were written for a View-based app. The superPlayer demo they are captured on is Jetpack Compose: its feed is a `LazyColumn`, there is no `RecyclerView`, and there is no `Application` subclass. We keep each plant's mechanism and change only where it lands, rather than adding View code the demo doesn't otherwise have:

- **Layout thrash** forces a re-measure of each visible feed item on every frame in the `LazyColumn`, instead of a forced `requestLayout` in a `RecyclerView` bind. It still targets `frame_p95_ms`.
- **Main-thread I/O on startup**: the plant's patch adds an `Application` subclass whose `onCreate` does the synchronous read. The plant is unchanged; it only brings its own `onCreate`.

Rejected: adding a `RecyclerView` screen to the demo just to host the plant. The measured screen would then exist only for the eval, which is not what an Android engineer's alert looks like. Affects `docs/roadmap.md` item 5 and issues #5 and #6.
