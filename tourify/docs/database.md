# Database

PostgreSQL + **PostGIS** (radius queries for "shows near me"). All tables have a UUID PK +
`created_at`/`updated_at`. ✅ = built; ⏳ = planned.

## Tables (built)

| Table | Key fields |
|---|---|
| `users` | `email`, `password_hash`, `display_name`, `bio`, `avatar_url`, `token_version` (bumped on password reset), `spotify_connected`, `discoverable` (global private mode, TD-9); home: `home_lat/home_lng/home_label`, `search_radius_km`; prefs: `notify_followed`, `notify_similar`, `notify_friends`, `notify_venues` |
| `artists` | `name` (canonical, native script), `romanized_name` (Latin display companion for non-Latin acts), `normalized_name`; identity: `musicbrainz_id`, `provider_ids` (JSONB: ticketmaster/lastfm/spotify), `match_confidence`; `image_url`; cached enrichment: `links` (JSONB), `bio` (Text), `tags` (JSONB) |
| `venues` | `name`, `city/region/country`, `geo` (PostGIS geography POINT), `latitude`/`longitude` (denormalized for serialization), `provider_ids` |
| `events` | `venue_id`, `title`, `starts_at`, `ticket_url`, `source` + `source_event_id` (unique dedupe key) |
| `event_artists` | `event_id` ↔ `artist_id`, `billing_order` (events can have multiple artists) |
| `user_artist_preferences` | `user_id` ↔ `artist_id` (follow); `source` (`manual`/`spotify_import`); unique per pair |
| `event_attendance` | `user_id` ↔ `event_id`, `status` (`interested`/`going`), `visibility` (`public`/`friends`/`private`); unique per pair |
| `artist_similarity` | `artist_a_id` → `artist_b_id` + `score`, `source` (`lastfm`); unique per pair — feeds "similar bands near you" |
| `notifications` | `user_id`, `type` (`followed_show`/`similar_show`/`friend_going`), `event_id`, `title`, `body`, `read_at`; unique per (user, event, type) |
| `friendships` | `requester_id`, `addressee_id`, `status` (`pending`/`accepted`); ordered unique pair + a Postgres `least/greatest` expression index so (a,b)/(b,a) can't coexist |
| `invites` | `user_id`, `code` (stable, reusable per user) — invite-link onboarding |
| `password_reset_tokens` | `user_id`, `token_hash` (SHA-256, never the raw token), `expires_at`, `used_at` — single-use, time-limited |
| `user_venue_preferences` | `user_id` ↔ `venue_id` (venue follow); unique per pair |
| `user_blocks` | `blocker_id`, `blocked_id` (directional rows, symmetric effect); unique per pair — safety floor (TD-9). Blocking removes any friendship |
| `reports` | `reporter_id`, `subject_type` (`user`…), `subject_id`, `reason`, `note`, `status` — capture-only |

## Tables (planned)

| Table | Notes |
|---|---|
| `push_devices` ⏳ | `user_id`, `expo_push_token`, `platform`, `device_id` — native push (Phase 3 remainder) |

## Migrations (Alembic)

`0001` initial (users, artists, venues, events, event_artists, preferences; enables postgis)
· `0002` event_attendance + events.title + venue lat/lng · `0003` artist_similarity · `0004`
artists.links · `0005` artists.bio/tags · `0006` notifications · `0007` notification prefs ·
`0008` friendships · `0009` users.spotify_connected · `0010` notify_friends pref · `0011`
invites · `0012` friendship_pair unique index · `0013` password_reset_tokens +
users.token_version · `0014` users.bio · `0015` users.avatar_url · `0016` user_venue_preferences
· `0017` artists.romanized_name (+ script-preserving normalized_name backfill) · `0018`
user_blocks · `0019` users.discoverable + reports · `0020` event_attendance.visibility default
→ public · `0021` users.notify_venues.

## Modeling notes

- **Artist reconciliation (TD-4).** Canonical identity = **MusicBrainz ID**; provider ids
  cached on the row. For "similar bands near you" a **normalized-name bridge** also links a
  Last.fm-similar artist to a Ticketmaster event artist when MBIDs don't align.
- **PostGIS from day one.** `venues.geo` (geography POINT) enables `ST_DWithin` radius
  filtering against a user's home; `latitude`/`longitude` are kept for easy serialization.
- **`event_attendance`** replaces plain saved-events (status + visibility), so a Phase 4
  social layer ("N friends going") is a query, not a rebuild.
- **Cached enrichment** (`artists.links/bio/tags`) is fetched lazily on artist-detail view
  and stored, so external calls (MusicBrainz/Last.fm) happen once per artist. `artists.bio`
  holds only the **lead paragraph** of the Last.fm wiki (not the whole article).
- **Script-aware names.** `artists.name` is the canonical/native-script name; a Latin
  `romanized_name` companion is stored for non-Latin acts (from MusicBrainz aliases) so cards
  can show "Native (Romanized)". `normalized_name` is Latin-folded for matching. See TD-8.

See also: [architecture.md](architecture.md), [api.md](api.md).
