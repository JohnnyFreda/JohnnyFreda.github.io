# Testing Considerations & Scenarios

A **living** doc of manual/exploratory test scenarios and known edge cases — it complements
the automated `pytest` suite (which covers pure logic + SQLite-safe API flows, but **not** the
PostGIS/geo and external-provider paths). Keep it current as features change.

> **Band data & disambiguation is the highest-risk area** (cross-provider identity is hard) —
> it gets its own section first.

## How to use this
- Work top-to-bottom for a release check, or jump to the feature you touched.
- ✅ = expected pass · ⚠️ = known quirk (documented, not a regression) · 🐛 = open issue.
- After changing a feature, **update the relevant scenarios here** (and add new ones).

## Test setup (dev)
- **Reseed demo data:** `cd backend && python -m scripts.seed_mock_friends` — creates your
  friends (Alex/Sam/Jordan), Friend Finder candidates (Maya/Priya/Devin/Leo), attendances,
  venue follows. Idempotent.
- **Seed a large scene (scale test):** `python -m scripts.seed_scene --per-city 100` (→ ~300
  users across Tampa/Denver/San Jose in taste clusters, with real band/venue follows +
  public attendances + a friendship graph; `--per-city 333` ≈ 1000). Tests that a **newly
  onboarded user gets Friend Finder suggestions** (needs a few band follows + a city — a truly
  empty user matches on proximity only) and that **social surfaces populate after adding
  friends** (friends-going / "Your scene" / activity feed / venue regulars — *not* the personal
  Discover feed, which is your own follows × location). Users live under `@seed.tourify.app`;
  **wipe with** `python -m scripts.seed_scene --wipe`.
- **View the DB:** pgAdmin/DBeaver → `postgresql://tourify:tourify@localhost:5432/tourify`
  (app tables are in the **`public`** schema; ignore `tiger`/`topology`). Or
  `docker exec -it tourify-db-1 psql -U tourify -d tourify`.
- **Backend must have provider keys:** run it with `uvicorn app.main:app --reload --env-file
  ../.env` (keys live in the root `.env`), else search/enrichment/similarity no-op. Event
  sources: `TICKETMASTER_API_KEY` (primary), `SEATGEEK_CLIENT_ID` (second aggregator). With
  only one set, the other silently no-ops — fine for dev.
- **Background jobs** (similarity refresh, region sync, alerts) only run in the worker —
  `python -m app.worker` — or via on-demand triggers (follow/location-set).
- **Reset password (no email):** `POST /auth/forgot-password {email}` returns the `reset_link`
  in dev; open it or `POST /auth/reset-password {token, new_password}`.

---

## 1. Band data & disambiguation  🎯

The pipeline on first artist-detail view: **bio/tags (Last.fm) → MBID verify/repair
(MusicBrainz) → links** (see TD-7/TD-8). Test via the app's artist page **and**
`GET /artists/{id}`.

### Reference artists (open each, verify)
| Artist | What to check | Notes |
|---|---|---|
| **Brand New** | Bio = the *rock band* intro paragraph only (no "There are two artists with this name" header, no wiki dump). MBID = `9311e2bc…` (rock), not the funk group. Links populated (Bandcamp/socials). No duplicate "Apple Music". | The canonical disambiguation test — Ticketmaster gave the *funk* MBID; the resolver repairs it by tag match. |
| **Монеточка / Сироткин / Гречка** (Cyrillic) | Native name shown with a `(romanized)` line (e.g. "Monetochka"). | Romanization from MB aliases (TD-8). |
| **112 / 311 / 5150** | ⚠️ digit-only names get flagged non-Latin → odd romanization ("One Twelve"/"Three Eleven") or none. | Known cosmetic quirk; candidate fix = treat letter-less names as Latin. |
| An obscure/indie act with **no MBID or Last.fm page** | Bio empty, tags empty, "No links found for this artist yet." No crash. | Enrichment is best-effort. |
| A **tribute act** (e.g. "Ultimate Coldplay") | Search returns it; following it syncs *its* events, attached to that artist. | Verify events don't bleed into the real artist. |

### Disambiguation checks
- [ ] Bio strips the "There are N artists with this name" header and keeps only the **lead
  paragraph** (not the full wiki).
- [ ] MBID repair only fires on a **same-name + tag-overlap** match (won't mis-pick a
  tagless/obscure act); never steals an MBID another artist row already owns.
- [ ] Links are **curated** (Discogs/IMDb/AllMusic dropped) and **deduped to one per platform**.
- [ ] Two genuinely different same-name artists **don't false-merge** (reconciler is
  MBID/provider-id first; name-only stays separate — TD-4).

### Known disambiguation issues / watch-outs
- ⚠️ Romanization is applied **on a repair only** → an already-correctly-identified non-Latin
  act needs the one-time backfill (done once; re-run if new such artists arrive).
- ⚠️ MBID repair needs Last.fm **tags** to disambiguate — but a **tagless** act with a single
  unambiguous exact-name MB entry is now auto-adopted (`pick_single_exact`, TD-8).
- ⚠️ Provider-supplied MBIDs can be wrong (the Brand New funk case) — always sanity-check
  links/bio consistency when a page looks off.
- ✅ **80 ACRES (resolved 2026-08-07):** no bio (Last.fm bio is *only* the "Read more" boilerplate
  → genuinely empty, correct), no tags (Last.fm has none), and no links — the bug. Cause: tagless
  act, so the tag-gated resolver wouldn't adopt its (single, exact) MB entry. Fixed by the tagless
  auto-adopt; also fixed a **cache-poisoning bug** where a transient MB timeout cached `links=[]`
  forever. Verify: 80 ACRES now shows name "80 Acres" + Website/Spotify/Apple/YouTube.
- ✅ **Belmont (resolved 2026-08-07):** bio rendered as `1.) Belmont is an American pop punk band…`
  — the disambiguation header was stripped but its **leading list enumerator `1.)` survived**.
  Cause: the enumerator regex only matched single-char `1.`/`1)`, not multi-char `1.)`. Fixed by a
  robust `_LEADING_ENUM` (`1.` `1)` `1.)` `(1)` `1 -`, and a final defensive strip for a `summary`
  that starts mid-menu with no "There are N…" header), guarded so a legit numeric start
  ("1980s synthpop…") is untouched. Verify: Belmont bio starts "Belmont is an American pop punk band".
- **Bio-cleanup checks (Last.fm):** open a **name-clash act** (a wiki with a "There are N artists
  with this name" header) and confirm the bio starts with real prose — **no `There are…` header,
  no leading `1.`/`1)`/`1.)`/`(1)` enumerator, no "Read more on Last.fm", lead paragraph only.**
- 🐛 *(log new disambiguation/bio bugs here — artist name + what's wrong. For acts the auto-resolver
  won't fix, use the dev "fix identity" panel; see §Dev tools below.)*

### Dev tools (admins only — `ADMIN_EMAILS`)
On the artist screen, admins get a dashed-amber **"Dev: fix identity"** panel:
- **Search MusicBrainz** → pick the correct entry → **Use this** pins the MBID and re-enriches
  (bio/tags/links resolve against it). For tagless/name-clash acts the auto-resolver won't touch.
- **Re-enrich (bust cache)** re-runs the whole pipeline for the current identity.
- Test: a **non-admin** account gets **403** on `/admin/*` and sees **no panel**; an allowlisted
  account sees it and can pin. MusicBrainz is rate-limited (1 req/s) — a 503 is transient, retry.

---

## 2. Auth & account
- [ ] Register (with a Name) / login / logout; refresh keeps you signed in.
- [ ] Password reset: forgot → open dev link → set new password → old password rejected (401),
  new works; the **reused token fails** (400); a **pre-reset session is logged out** (401).
- [ ] Edit profile: display name, bio, avatar (upload/change/remove). ✅ email **never** shown
  to other users (check any friend/other surface).

## 3. Discovery (compendium)
- [ ] Set home location (geocode pick-list). Discover shows **Your bands**, **Similar to music
  you like**, **At venues you follow** sections.
- [ ] "Similar to you" is empty if similarity isn't cached — run the worker or re-follow (known
  cold-start; see setup). After: similar shows appear.
- [ ] Mark Going/Interested; it appears in My Music; the **visibility picker** (Public/Friends/
  Only me) works and defaults to **Public**.
- [ ] Map toggle plots followed + similar + venue events.

## 4. Venues (first-class)
- [ ] Follow/unfollow a venue; it appears in My Music → Venues.
- [ ] Venue card: details, map, upcoming shows, follower count, **Friends who follow**,
  **Regulars** (top public attendees; ⚠️ private-mode + blocked users must NOT appear).
- [ ] Venue name on an event page is tappable → venue screen.
- [ ] Venue-show alerts: with `notify_venues` on, evaluating alerts creates `venue_show`
  notifications for followed-venue shows (no home location required).

## 5. Social — friends
- [ ] Add by email; invite link (share → open → auto-friend). Requests: accept/decline.
- [ ] Friend cards show **N mutual friends · M mutual bands**.
- [ ] Activity feed: recency-ordered; going/interested breakdown; avatars; tap → event.
- [ ] Friend profile: bio, top bands, going/interested, mutuals. Tap a friend anywhere.
- [ ] "Friends going" on an event; "Friends following" on artist/venue pages.

## 6. Friend Finder (suggestions)
- [ ] "People you may know" shows named candidates with **reasons** (mutual friends / shared
  venues / bands in common / near you), sorted by strength.
- [ ] Tapping a suggestion opens their **public profile** (not "User not found").
- [ ] **Add** sends a request (by user_id); they leave the list.
- [ ] Excludes: yourself, existing friends + pending, blocked (both ways), private-mode users.

## 7. Safety (TD-9)
- [ ] Block from a user's profile → they're removed as a friend, can't re-request either way,
  disappear from your surfaces + suggestions + venue regulars.
- [ ] Unblock (Profile → Privacy → Blocked users) restores the ability to connect.
- [ ] **Private mode** (Discoverable off): you drop out of Friend Finder + non-friends'
  discovery surfaces; app still fully usable.
- [ ] Report a user (reason picker) → 201; a `reports` row is written (capture-only).
- [ ] Attendance visibility: Public shows to everyone; Friends only to friends; Only-me hidden.

## 8. Avatars & media
- [ ] Upload jpeg/png/webp ≤5MB → avatar shows everywhere (profile, friends list, feed stack,
  regulars). Non-image or >5MB → rejected. Remove → back to initials.

## 9. Notifications
- [ ] Bell unread badge; inbox marks read on open; per-type prefs gate alerts (followed /
  similar / friends / venues); tapping a notification deep-links to the event.

## 10. Ingest & cross-source dedup (TD-10)  🎯

Multi-source ingest is the other high-risk area: two sources for one show must **not** become
two rows. Pure matching logic (`pick_venue_match`) is unit-tested; the DB reconciliation path
touches PostGIS/JSONB so it's **verified live against Postgres**, not SQLite.

- [ ] **Same show, two sources → one row.** Ingest a Ticketmaster show + a SeatGeek copy (same
  venue, artist, date) → **1 event + 1 venue**, each with both ids in `provider_ids`. (Scripted
  live check lives in the commit that added TD-10; re-run pattern: ingest two `ProviderEvent`s,
  assert single rows + merged provenance.)
- [ ] **TBD/midnight vs known start time** still matches (±12 h window).
- [ ] **Idempotent:** re-ingesting the same source twice never creates a second row.
- [ ] **No shared MBID** (the indie case): SeatGeek gives no MBID and TD-4 won't name-merge
  artists, so the band may be two artist rows — the **event still dedupes** because
  `find_cross_source` bridges on artist *normalized name* (TD-6), not artist id. Verify a show
  by an MBID-less indie band from both sources collapses to one event.
- [ ] **Venue matching:** same normalized name + within 250 m (or same city when coords
  missing) → merged; **same name in a different city → separate** (no false merge). ⚠️ spelling
  variants ("The Fillmore" vs "Fillmore Auditorium") stay separate until a merge tool exists.
- [ ] **Owning vs secondary source:** the primary source refreshes its own title/`starts_at`
  (reschedules); a secondary source **only fills blanks** — it must never clobber the primary's
  values. Verify a SeatGeek re-ingest doesn't overwrite a Ticketmaster title.
- [ ] **Venue-less crowdsourced show** falls back to the per-source key (no false cross-match).
- [ ] **Ticketmaster coverage:** Discovery already includes **TicketWeb + Universe** (indie/club
  self-serve) — no `source` filter needed; confirm club shows appear. Region sync now **pages**
  past the ~199/page cap (bounded by TM's 1000-result ceiling) — spot-check a dense market pulls
  more than 199.
- 🐛 *(log new dedup/merge bugs here — the artist/venue/show + what mismatched or double-listed.)*

## 11. Mobile / on-device testing  📱

Most testing so far is **web-first** (Expo web). Real devices exercise things the browser can't:
native gestures, keyboards, safe areas, secure storage, the share sheet, and external-app
hand-offs. This app has **no Expo Go blockers** (SDK 52; only expo-router/-image-picker/
-secure-store/-constants/nativewind — all Expo-Go-compatible), so start there.

### Device setup (do this first — shared by every device option)
Phones can't reach `localhost`; they hit this machine over Wi-Fi.
- [ ] **Same Wi-Fi** for phone + dev machine (router must allow client-to-client traffic).
- [ ] Backend bound to LAN: `uvicorn app.main:app --reload --host 0.0.0.0 --env-file ../.env`.
- [ ] Start Expo pointed at the machine: `EXPO_PUBLIC_API_URL=http://<LAN-IP>:8000 npx expo start`
  (find the IP with `ip route get 1.1.1.1`; it can change between sessions).
- [ ] **Expo Go** app: iPhone via App Store (scan QR w/ Camera); Android via Play Store (in-app
  scanner). **Min OS: iOS 15.1+ / Android 7.0+** (RN 0.76 floor — an older tablet can't run it;
  fall back to the mobile browser at `http://<LAN-IP>:8081`).
- [ ] Sanity: can log in on device (proves the phone reaches the API — the #1 gotcha if it fails).

### On-device checks (things web can't fully verify)
- [ ] **Auth persistence:** log in → force-quit → reopen → still signed in (`expo-secure-store`,
  not localStorage). Token refresh works; a password reset logs the device out (`ver` claim).
- [ ] **Avatar upload from a real device:** pick from **library** *and* take a **photo**
  (`expo-image-picker` permission prompt appears; deny → graceful). Upload → shows everywhere.
- [ ] **Invite link share sheet:** "Share an invite link" opens the **native share sheet** (not
  the web clipboard path); send to another device → deep link opens the app → auto-friends.
- [ ] **Deep links:** tapping a notification / invite / friend / venue routes correctly from a
  cold start *and* when the app is already open.
- [ ] **External hand-offs:** **Tickets** opens the browser; **Connect Spotify** opens the OAuth
  page and returns; **"Open in Maps"** launches the native maps app.
- [ ] **Keyboards & inputs:** email keyboard for email, password masking + the eye-toggle, Return
  advances/submits; the keyboard doesn't cover the focused field (auth, search, bio, location).
- [ ] **Safe areas & layout:** notch/Dynamic Island + home-indicator insets on the header, tab
  bar, and modals; nothing clipped. Both **portrait** and the tablet's likely **landscape**.
- [ ] **Gestures & scroll:** the new Discover **horizontal rails** scroll smoothly and don't fight
  vertical scroll; pull-to-refresh works; long lists stay smooth (`My Music`, activity feed).
- [ ] **Maps:** native uses the **fallback** (no `react-native-maps` installed yet) while web uses
  Leaflet — confirm the Discover Map toggle + venue/event maps degrade sensibly on device.
- [ ] **Two-device social loop:** iPhone + tablet as two accounts — friend request → accept →
  "friends going" / activity feed update; block hides both ways. Real end-to-end social test.
- [ ] **Theme/perf:** dark theme renders true-black (no web scrollbar artifacts); images load;
  no jank on mid-range/old hardware.

### Known limits / not-yet-testable on device
- ⚠️ **Push notifications don't work in Expo Go** — needs a **dev build** (`eas build -p android
  --profile development`, free, no account) once `expo-notifications` lands. **In-app** bell/inbox
  alerts *do* work in Expo Go; only remote push needs the build.
- ⚠️ **iOS beyond Expo Go** (dev build / TestFlight / iOS push) needs the **$99 Apple Developer**
  account — deferred per the roadmap; a free local Xcode build works but the cert expires weekly.
- ⚠️ **Web-only affordances** (Enter-to-submit, Caps-Lock hint — see the backlog)
  are irrelevant on device; don't flag their absence as a mobile bug.
- 🐛 *(log device-specific bugs here — device/OS + what broke; note if web-only or native-only.)*

---

## Regression watch-list (things that have broken before)
- Adding a table/column that a **social query** touches → update the relevant **SQLite test
  fixtures** (e.g. `user_blocks`, `user_artist_preferences` must exist wherever `/me/friends`
  or friend-request flows are exercised).
- **Server-side enforcement** of blocks + private mode on **every** people-surface (TD-9) —
  re-check when adding a new surface that lists other users.
- Bio/links **caching**: changes to `_clean_bio`/links only affect *new* fetches; existing rows
  need a backfill (clear `tags`/`links` to re-trigger, or a script).

## Maintenance
This doc is a living artifact — **update it in the same change** that alters a feature. Log new band-data/disambiguation bugs in §1's issue list.

See also: [technical-decisions.md](technical-decisions.md) (TD-4/7/8/9),
the phase plan, the milestones.
