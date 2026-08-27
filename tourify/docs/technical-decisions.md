# Technical Decisions

Record of non-obvious engineering decisions, with rationale. Complements
[architecture.md](architecture.md), [backend.md](backend.md), and
[database.md](database.md).

## TD-1 — Background job runner: APScheduler first

Two kinds of work: **scheduled/periodic** (event sync, similarity refresh) and
**on-demand/triggered** (set location → sync area; follow artist → fetch tour; Spotify
import → batch fetch; send push).

**Decision:** start with **APScheduler** in a dedicated worker process, using a
**Postgres jobstore** (survives restarts). Jobs are written as plain **service functions**
behind a thin job-service abstraction, so the runner is swappable. On-demand triggers call
the same functions.

- **Infra stays minimal:** Postgres + API + worker; no Redis yet.
- **Evolution:** introduce a Redis-backed queue (**arq** or Celery) at **Phase 3**, when
  alerts need reliable retries/fan-out (Redis can also serve caching then).
- **Rejected (for now):** Celery/arq + Redis from day one — stronger "distributed systems"
  portfolio signal, but more infra than the early phases justify.

## TD-2 — Event sync strategy: hybrid (region + artist)

The two headline features need different data shapes, so sync is hybrid.

- **Region sync (local universe):** periodically pull upcoming **music** events within each
  active user's home area, keyed by **market/geohash** so many users in one city = one
  sync. Powers "similar bands near you", discovery, and the cold-start fallback.
- **Artist sync (followed tours):** for each followed band, pull its **entire upcoming
  tour** (not just local) — answers "is my band touring / nearest date" and serves the
  Music Tourist.
- **On-demand triggers** (via TD-1) keep it fresh: set/change location → region sync now;
  follow artist → tour fetch now; Spotify import → batch fetch.

**Rate/volume:** Ticketmaster free tier (~5k req/day, 5 req/s); market/geohash keying and
per-artist caching keep it well within limits at portfolio scale. Cadence: periodic
refresh + on-demand top-ups.

## TD-3 — Cold start: never show an empty Discover

- Onboarding **requires home location** (minimum input for any local data).
- Hard-funnel to **Spotify import** or "follow a few bands" (import is the cold-start hero).
- If the user still follows nothing, **Discover falls back to "popular / soon near you"**
  from region-synced data, plus a prompt to follow. Discover is never blank once location
  is set.

## TD-4 — Artist reconciliation: MusicBrainz-anchored canonical identity

Same band arrives from Ticketmaster (attractionId), Last.fm (name/MBID), Spotify (id) and
must collapse to **one** canonical `Artist` without duplicating or false-merging.

**Decision:** anchor on **MusicBrainz IDs (MBID)** as canonical identity, with provider-id
caching + name-match fallback. Ingest pipeline:
1. **Seen this provider id before?** → existing artist (common case, O(1)).
2. **New artist:** resolve an **MBID** — Last.fm often returns one; bridge Ticketmaster
   (`externalLinks`) / Spotify (id) into a MusicBrainz lookup.
3. **No confident MBID?** → **normalized-name** match (lowercase, strip
   punctuation/diacritics), but **auto-merge only on high confidence**; otherwise create a
   distinct row.
4. Store every discovered provider id + the MBID on the canonical row (one-time cost per
   artist, cached forever).

- **MusicBrainz** becomes a **reconciliation service** (not an `EventProvider`): free,
  rate-limited (1 req/s, requires a descriptive User-Agent). Fine — reconciliation runs
  once per artist at ingest and is cached.
- **Merge-safety bias:** favor **avoiding false merges**. A duplicate is annoying but
  recoverable via a later merge tool; a false merge corrupts two bands' data. So name-only
  matches stay separate unless high-confidence.

## TD-5 — Alerts: in-app first, channel-agnostic pipeline

Alert evaluation **reuses the discovery queries** (followed-near-home + similar-near-home)
and creates deduped `Notification` rows (unique per user/event/type), gated by the user's
per-type prefs. It runs on follow, on location-set, and in the periodic worker.

**Decision:** ship the **in-app** channel first (bell + inbox) — fully demoable with **no
$99 Apple gate**. Native push (Expo→APNs/FCM) and email are added later as
`NotificationChannel` impls; the pipeline is already channel-agnostic.

## TD-6 — "Similar near you": normalized-name bridge

Requiring a shared MBID between a Last.fm-similar artist and a Ticketmaster event artist
made "similar to you" very sparse. **Decision:** also **bridge on normalized artist name**
in the similar-discovery join, and pull the **full Ticketmaster page (~199)** in region
sync for more local candidates. This lifted results materially (≈1 → ≈8 in testing) while
staying bounded by real data (how many similar artists actually have local shows).

## TD-7 — Artist enrichment: lazy fetch + cache on the row

Links (MusicBrainz URL rels + Spotify), bio, and tags (Last.fm) are **fetched on first
artist-detail view and cached** on the `artists` row (`links`/`bio`/`tags`). Rationale:
avoids repeated rate-limited external calls, keeps search/list endpoints cheap, and works
by artist **name** (so bio/tags cover artists that lack an MBID). The pipeline runs in
order — **bio/tags → MBID verify (TD-8) → links** — so link/identity lookups use the
corrected MBID. Details: links are **curated by domain** (aggregator/database URLs —
Discogs, IMDb, AllMusic… — are dropped) and **deduped to one per platform label** (Last.fm
/ MusicBrainz can return several regional Apple Music URLs). The **bio is the Last.fm wiki's
lead paragraph only** — the full `content` is the whole article; a leading "There are N
artists with this name" disambiguation header is stripped.

## TD-8 — MBID verify/repair + romanization

Providers sometimes hand us the **wrong** MusicBrainz id for a name-clash artist
(Ticketmaster tagged the rock band *Brand New* with the *funk* group's MBID, so its
MusicBrainz links came back empty). And non-Latin acts arrive under a romanized provider
name that doesn't match MusicBrainz's native-script canonical name.

**Decision:** on enrichment, when we have Last.fm **tags**, search MusicBrainz by name and
pick the **same-name candidate whose tags best overlap ours** (matching on canonical name,
sort-name, **or any alias** — this is what bridges a romanized provider name to a native
canonical). On a confident repair, adopt that MBID, the **native-script canonical name**,
and a Latin **`romanized_name`** for display; then invalidate the cached bio/tags/links so
they re-fetch under the right identity.

- **Conservative:** only repairs on a real same-name + tag-overlap match; never steals an
  MBID already owned by another row. Consistent with TD-4's merge-safety bias.
- **Tagless fallback (`pick_single_exact`):** when Last.fm gives **no tags** (nothing to
  overlap on), adopt an MBID only if MusicBrainz has **exactly one** exact-name, high-score
  (≥95) candidate — unambiguous. Two same-name candidates → refuse (leave to the manual
  tool). This fixed *"80 ACRES"* (a real 6.7k-listener act with no Last.fm bio/tags but a
  clean single MB entry): it was stuck with no MBID → no links; now it auto-adopts
  `019af4ba…`, corrects the display name, and pulls website/Spotify/Apple/YouTube.
- **Manual dev override:** the auto-resolver *correctly* refuses ambiguous/low-signal cases,
  so there's always a tail it won't touch. `POST /admin/artists/{id}/mbid` (dev-gated to
  `ADMIN_EMAILS`; plus `mb-candidates` search + `reenrich`) lets a human pin the right entry
  and re-enrich — surfaced as a dev-only "fix identity" panel on the artist screen. See
  [testing.md](testing.md) §1.
- **Cache-poisoning fix:** a *transient* MusicBrainz failure (timeout/503) used to cache
  `links=[]` permanently. Now `_fetch_mb_urls` raises on failure and the links service
  **doesn't cache** — it leaves `links=None` to retry next view; a genuine no-relations 200
  still caches `[]`. (Last.fm bio/tags already behaved this way.)
- **Gap:** romanization is applied on a *repair/adopt*, so already-correctly-identified
  non-Latin acts need a one-time backfill (done once). Fuzzy-name matching + a bulk
  merge/admin tool remain future work.

## TD-9 — Visibility & privacy: public-first, tiered, safety-first

Co-pillar means real-world social data (attendance, connections) at low *and* high user
counts. The vision ([vision.md](vision.md)) commits to **public-first (opt-out)** to make
scene discovery and the social cold-start work, but **tiered** to protect real-world safety.

**Decision:**
- **Public by default (opt-out):** identity (name/avatar/bio), taste (followed
  artists/venues), and **attendance** (going/interested) — the "who's going" that powers scene
  discovery and *Venue-as-home-base*. Default `EventAttendance.visibility` becomes **`public`**
  (currently `friends`); the per-attendance control (`public`/`friends`/`private`) stays, plus
  a global **private mode** on the user.
- **Never public:** precise/home location. A show's *venue* is inherently public; the user's
  whereabouts are not. Coarse city/scene only.
- **Safety is first-class scope, not later:** **Block & report** gates opening social beyond
  testers. A block is **symmetric** and enforced **server-side on every social query** —
  friends, activity feed, friends-going/following, mutual counts, profiles, discovery,
  suggestions — never UI-only. (Today `FriendUser` already excludes email; this extends the
  same server-side discipline to blocks.)

**Why public-first over private-first:** with no users, a private-first graph is a dead empty
room; public identity + attendance lets people find their scene *before* their friends join,
while the compendium already carries solo/N=1 value. The cost is a larger safety surface, paid
down by the controls above.

- **Implementation note:** flipping the attendance default to `public` is a small change
  (schema default + the existing visibility mechanism), but **must not ship before Block &
  report + a global private mode** — otherwise it's a trap, not a default.

## TD-10 — Cross-source ingest: deliberate dedup & reconciliation (no merge conflicts)

Adding a **second event source (SeatGeek)** beside Ticketmaster — and every future ingest
(scraped JSON-LD/iCal, crowdsourced flyers, more ticketers; see
the data-sources notes) — means the *same real-world entity* now arrives from
multiple sources. Source-local ids are **not** stable identity, so keying rows on them alone
duplicates venues and shows (two cards for one gig). This is a standing design rule, not a
one-off: **every ingest reconciles to a canonical entity before insert.**

**Decision — a shared match ladder for artists, venues, and events:**
1. **Stable global id** when present (artist **MBID** — TD-4).
2. **Provider id already on a canonical row** (the `provider_ids` provenance map).
3. **Cautious cross-source natural key** (bias against false merges — TD-4):
   - **Artist:** normalized name, high-confidence only (still won't auto-merge on name alone).
   - **Venue:** `normalized_name` + **geo proximity** (≤250 m) when both have coords, else same
     **city**. Pure `pick_venue_match()` so it's unit-testable without PostGIS.
   - **Event:** same **venue** + **date (±12 h**, to tolerate a known start vs a TBD/midnight
     placeholder) + an artist matching by **normalized name**. We bridge on the artist *name*
     (TD-6), **not** the canonical artist id: a second source rarely shares an MBID and TD-4
     won't name-merge artists, so the same indie band is often two artist rows — matching the
     name still collapses the duplicate show.
4. **Else** create a new canonical row.

**Provenance & conflict resolution:**
- Every canonical row carries a `provider_ids` **map** (`{source: source_id}`). Artists and
  venues already had it; **events** now do too (`0022`), alongside the primary
  `source`/`source_event_id` kept for display + the unique constraint.
- On a match, **merge provenance** (`provider_ids[source] = id`) so re-ingest updates, never
  duplicates — **idempotent**.
- **The owning source** (the one in the event's `source` column) may refresh its own scalar
  fields (title, `starts_at` reschedules, ticket url). A **secondary** source **enriches only
  — fills blanks, never clobbers** a value the primary already set. Venues, which have no
  single owning-source column, are always fill-blanks. Rationale (TD-4): a duplicate or a
  slightly stale field is recoverable; a false merge or a secondary clobbering the primary
  corrupts data.

**Why this is a gate, not a nice-to-have:** without it, turning on SeatGeek fan-out (region +
per-artist sync) would immediately double-list every arena show both sources carry. Verified
live on Postgres: a Ticketmaster show + a SeatGeek copy (same room, TBD time, no shared MBID)
collapse to **one** event + **one** venue with merged `provider_ids`.

- **Known trade-offs / debt:** venue matching is name+geo/city only (no fuzzy-name yet), so
  spelling variants ("The Fillmore" vs "Fillmore Auditorium") create separate rows until an
  admin **merge tool** exists (future work); a venue rename won't propagate under fill-blanks.
  Event dedup needs a venue on both sides — venue-less crowdsourced shows fall back to the
  per-source key. These are intentionally conservative (dup over false-merge) and revisited
  when a merge/admin tool lands. See test scenarios in [testing.md](testing.md) §Ingest. The
  merge tool + connector staging that pay this down are designed in
  a separate design doc (§5 merge tools, §2 staging).

### Venue de-dup & disambiguation — considerations (the harder cousin of event dedup)
Real case (Aug 2026): **two "Jannus Live" rows**, both from **Ticketmaster** (different TM venue
ids), ~100 m apart, cities "St Petersburg" vs "Saint Petersburg". ~30 such dup pairs exist.
- **Why they slipped through:** `pick_venue_match` *would* catch this now (same `normalized_name`,
  ≤250 m), but **TD-10 only dedups at ingest** — these rows **predate migration 0022**, and nothing
  cleans up **pre-existing** dupes. → need a **one-time backfill dedup pass**, not just
  go-forward prevention.
- **Same-source dupes are real** — Ticketmaster itself keeps two venue records for one room, so
  dedup can't lean on "one id per source"; the name+geo match is doing the real work.
- **Venues lack a stable global id.** Artists anchor on **MBID**; events on a natural key
  (venue+date+artist). Venues have only **name + geo** — no authoritative id — so they're the
  *hardest* entity to disambiguate. A future enrichment could adopt a **Wikidata / OSM venue id**
  as the canonical "venue MBID" for airtight dedup.
- **City-string normalization** (St ↔ Saint, St. ↔ St, abbreviations) would strengthen the
  coord-less fallback (the 3 venues with no coords).
- **Fuzzy name** ("Jannus Live" vs its old "Jannus Landing") is the standing debt — helps, but
  risks false merges, so **human-confirm**, not auto.
- **Shipped (Aug 2026):** `backend/scripts/dedup_venues.py` — clusters venues by `normalized_name`,
  **auto-merges only high-confidence**, **reports ambiguous clusters for review** (bias against
  false merges — two real rooms can share a name, e.g. chain venues). It merges the loser into the
  richest row (most events, then follows): reassigns `events` + `user_venue_preferences` +
  **`venue_vibe_tags`** (deduping the unique constraints), unions `provider_ids`, fills winner
  blanks, deletes the loser — the venue merge primitive from a separate design doc
  §5. Dry-run by default; `--apply` to execute. First run: **28 clusters auto-merged, 2 held**
  (The Ritz Raleigh/NC vs San Jose/CA — different rooms; Hollywood Bowl — Hollywood vs LA), 0
  orphaned events. Go-forward, TD-10 already prevents new dupes.
- **The "high-confidence" signal is `normalized_name` + same city + same region — NOT tight geo.**
  The original plan was "same name + within ~150 m," but **provider venue coordinates are
  unreliable**: the two rows of the same room are routinely km apart (Red Rocks 8 km, The Ritz Ybor
  18 km). Tight geo would have merged almost nothing. Same normalized name + same normalized city
  (Saint↔St) + same region is the strong same-venue signal; a generous distance cap (~40 km) is
  only a sanity backstop. Different city or region → held for human review (chain-name collisions).
- **`provider_ids` is one-id-per-source (a modeling limit).** A venue with **two same-source ids**
  (TM's dup records) can't store both in `{source: id}` — a merge keeps one, and the other's future
  re-syncs re-match by name+geo (no dupe row, but the *stored* id can flip-flop between the two on
  alternating syncs — cosmetic, doesn't misattach events). An **array-per-source**
  (`{source: [ids]}`) models it correctly, but `provider_ids` is shared by **Venue + Artist +
  Event** with lookup (`provider_ids[source].astext == id` → JSONB array-contains) and merge logic,
  so it's a **cross-entity refactor** — reserve it for when same-source dupes prove common, and do
  it consistently across all three (not venue-only). The stronger long-term fix is a **canonical
  external venue id** (Wikidata/OSM) — a real global anchor that dedups authoritatively and
  sidesteps same-source-id fragility entirely.
