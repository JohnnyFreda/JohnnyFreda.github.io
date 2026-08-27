# Backend

FastAPI modular monolith. Layering: **router → service → repository**, with external
integrations behind **providers**.

```
app/
  api/routes/    auth, artists, events, friends, venues, geocode, me, onboarding, health
  services/      catalog, discovery, similarity, sync, ingest, reconcile, musicbrainz,
                 location, attendance, alerts, onboarding, bio, links, geocoding,
                 friends, venues, avatars, email
  repositories/  user, artist, venue, venue_preference, event, preference, attendance,
                 similarity, notification, friendship, invite, password_reset (+ _geo helper)
  providers/     base (interfaces + DTOs), ticketmaster, lastfm, spotify
  models/        SQLAlchemy models      core/  config, database, security, text
  worker.py      APScheduler worker     migrations/  Alembic
```

## Providers (external integrations)

- **`EventProvider`** → **Ticketmaster** (`ticketmaster.py`): artist search, artist events,
  events-near-geo. Parsing is pure/unit-tested. Reconciles artists via `provider_ids`/MBID.
- **`RecommendationProvider`** → **Last.fm** (`lastfm.py`): `artist.getSimilar` (similarity)
  and `artist.getInfo` (bio + genre tags). Own engine remains a post-MVP option.
- **Spotify onboarding client** (`spotify.py`): Authorization-Code OAuth + Get User's Top
  Artists — import only, **not** similarity (those endpoints are deprecated for new apps).
- **MusicBrainz** (via `services/links.py` + `services/musicbrainz.py`): URL relations for
  artist links, the reconciliation anchor (MBID), and **identity verify/repair** by tag match
  (+ romanization, TD-8). Rate-limited (1 req/s, needs a User-Agent).
- **Nominatim** (`services/geocoding.py`): free geocoding for the location pick-list.

## Notable services

- **reconcile** — upsert/merge artists across providers (MBID first, provider-id, then a
  cautious normalized-name path).
- **ingest** — upsert venues/events/artist links from provider payloads.
- **sync** — hybrid event sync (region + per-artist tours); best-effort.
- **similarity** — fetch + cache `ArtistSimilarity` from Last.fm.
- **discovery** — followed-near-home + similar-near-home (PostGIS `ST_DWithin`; similar uses
  a normalized-name bridge).
- **alerts** — reuses the discovery queries to create in-app notifications, gated by the
  user's notification prefs.
- **links / bio / musicbrainz** — lazily enrich an artist on detail view (bio/tags → MBID
  verify/repair + romanization → curated, deduped links), all cached on the row (TD-7, TD-8).
- **onboarding** — import Spotify top artists as follows, bridging each to Ticketmaster by
  name for event coverage.
- **friends** — friend requests/accept/decline/remove, invite links (get/redeem), the
  recency-ordered activity feed, mutual friends/bands counts, and friend profiles
  (friends-only; email never exposed).
- **venues** — follow/unfollow venues + the venue card (upcoming shows, follower count,
  friends who follow).
- **avatars / email** — avatar upload validation + local-disk storage (object-storage seam);
  `EmailSender` (`ConsoleEmailSender` in dev / `SmtpEmailSender` in prod), used by password
  reset and future alert emails.

## Background worker

`app/worker.py` — **APScheduler `AsyncIOScheduler`**, one periodic `refresh_all` job
(`EVENT_SYNC_INTERVAL_HOURS`, default 6): region sync per distinct home area, per-followed
tour sync + similarity refresh, then alert evaluation for every user with a home location.
No-ops cleanly when provider keys are absent. On-demand triggers (follow, location-set,
Spotify import) call the same service functions synchronously so the UI updates immediately.

> Notification delivery is currently **in-app only** (`Notification` rows + inbox). A
> `NotificationChannel` abstraction for **native push** (Expo→APNs/FCM) and **email** is the
> Phase-3 remainder; the alert-evaluation pipeline is already channel-agnostic.

## Auth

Hand-rolled JWT (access + refresh, PyJWT) + bcrypt password hashing. Chosen over a managed
provider to demonstrate the mechanics and avoid an external dependency. **Password reset**
uses single-use, SHA-256-hashed tokens (no enumeration; dev returns the link since email is
optional). Tokens embed a `ver` claim = `users.token_version`, bumped on reset, so a reset
**invalidates every outstanding session**. Other users are exposed by display name + avatar
only — **never email**.

## Conventions

Strict typing; Ruff + Black; Pytest (parsing/crypto unit tests + auth API tests over
SQLite). See [coding-standards.md](coding-standards.md).
