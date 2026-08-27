# Glossary

- **Artist** — a canonical band/musician record. Reconciled across sources via
  `provider_ids` (Ticketmaster, Last.fm/MusicBrainz, Spotify).
- **Event** — a specific show: artist(s) + venue + date/time, with source + ticket URL.
- **Venue** — a physical location with geo coordinates (PostGIS) for radius search.
- **Follow** (`UserArtistPreference`) — a user marking an artist as a favorite; sourced
  `manual` or `spotify_import`.
- **Attendance** (`EventAttendance`) — a user's `interested`/`going` status on an event,
  with visibility; the signal the social layer reads.
- **Provider** — an external data source behind an interface: **EventProvider**
  (Ticketmaster…), **RecommendationProvider** (Last.fm / own engine).
- **Similarity** (`ArtistSimilarity`) — cached artist-to-artist scores (Last.fm) driving
  "similar bands near you"; matched to local events via MBID **or a normalized-name bridge**.
- **Reconciliation** — collapsing the same band across providers into one canonical
  `Artist`, anchored on **MusicBrainz ID** (TD-4).
- **Notification** — an in-app alert (`followed_show` / `similar_show`) created by the
  alert-evaluation job; shown in the bell + inbox. **Channels** (native push, email) are the
  Phase-3 remainder.
- **Enrichment** — cached artist extras fetched lazily on the detail view: **links & merch**
  (MusicBrainz URL rels + Spotify, curated), **bio** + **tags** (Last.fm).
- **Discovery** — nearby shows by followed + similar artists (two sections).
- **My Music** — the user's hub: upcoming going/interested shows + followed bands.
- **Invite** — a share link that auto-connects a new user as a friend (Phase 4 social).

See also: [database.md](database.md), [architecture.md](architecture.md).
