# Architecture

Tourify is a **modular monolith**: a single deployable FastAPI application organized
into feature modules, each following the repository → service → provider layering.
This keeps the codebase easy to reason about and demo (a portfolio goal) while the
provider seams leave room to grow toward the indie-coverage north star.

**Mobile + push notifications is an explicit product goal**, so the client is a native
mobile app (Expo/React Native) with native push as a first-class channel.

## Stack

- **Backend:** FastAPI (Python), modular monolith, client-agnostic REST
- **Database:** PostgreSQL + **PostGIS** (radius/geo queries for "shows near me")
- **Frontend:** **Expo (React Native), single codebase** → iOS + Android native + web
  (react-native-web); feature-first, strict TypeScript
- **Push:** native via **Expo Notifications → APNs/FCM** (first-class channel)
- **Background jobs:** scheduled workers for event sync, similarity refresh, alert evaluation
- **Tooling:** Ruff, Black, Pytest; strict typing, tests, linting

## Diagram

```
                 ┌─────────────────────────────────────────┐
                 │     Expo app (iOS · Android · web)        │
                 │  React Native, feature-first, strict TS   │
                 └───────────────┬───────────────────────────┘
                                 │  REST (client-agnostic)
                 ┌───────────────▼───────────────────────────┐
                 │              FastAPI monolith               │
                 │  modules: auth · artists · events ·         │
                 │  discovery · recommendations · alerts ·     │
                 │  notifications · onboarding · social(P4)    │
                 │                                             │
                 │  each module: router → service → repository │
                 │  external calls → provider interfaces       │
                 └───┬───────────────┬───────────────┬─────────┘
                     │               │               │
           ┌─────────▼──┐   ┌────────▼─────┐   ┌─────▼──────────┐
           │ PostgreSQL │   │  Providers   │   │  Notification  │
           │ + PostGIS  │   │ TM · Last.fm │   │   channels     │
           └────────────┘   │ · Spotify ·  │   │ native push ·  │
                            │  MusicBrainz  │   │ email          │
                            └──────────────┘    └────────────────┘

  Background worker (APScheduler): event sync (region + artist) ·
  similarity refresh · alert evaluation
```

## Key abstractions (the load-bearing seams)

These three interfaces are where the design flexes over time. Nothing above them
should know which concrete implementation is in use.

- **`EventProvider`** — `search_artists`, `get_artist_events`, `search_events_near`. Current
  impl: **Ticketmaster**. Per-artist sync **fans out** over `get_event_providers()`, so a
  secondary/indie source drops in without touching callers — but that seam is **currently
  unfilled**: Bandsintown (the intended indie source) shut down its public API and was
  removed. Cross-source reconciliation happens via `Artist.provider_ids` + MBID.
- **`RecommendationProvider`** — `similar_artists(artist) -> [ScoredArtist]`.
  Impl: **Last.fm** (`artist.getSimilar`; also `artist.getInfo` for bio/tags). "Similar
  bands near you" additionally **bridges by normalized artist name** when a Last.fm-similar
  and a Ticketmaster event artist don't share an MBID. Own engine remains a post-MVP option.
- **Artist reconciliation + enrichment** — collapses the same band across providers into one
  canonical `Artist`, anchored on **MusicBrainz IDs** (TD-4). On artist-detail view, a lazy
  **enrichment pipeline** runs once and caches: bio/tags (Last.fm) → **MBID verify/repair**
  against MusicBrainz by tag match, which also adopts the native-script name + a
  `romanized_name` (TD-8) → curated links (TD-7). MusicBrainz is a reconciliation dependency,
  not an `EventProvider`.
- **`NotificationChannel`** — `send(user, notification)`. **Currently in-app only**
  (`Notification` rows + inbox); **native push** (Expo → APNs/FCM) and **email** are the
  Phase-3 remainder. The alert-evaluation job is already channel-agnostic, so channels slot
  in without touching the pipeline.

## Design principles

- **Client-agnostic API.** No client-specific logic leaks into FastAPI; the same backend
  serves the Expo app across iOS, Android, and web.
- **Own the data.** Providers sync into Postgres via background jobs; the UX queries our
  own DB (fast, geo-filterable, and decoupled from third-party rate limits/outages).
- **Thin external edges.** Spotify (onboarding) and any single provider can shift or
  break without touching core flows.

See also: [backend.md](backend.md), [database.md](database.md), [api.md](api.md),
the roadmap.
