# PRD

Product requirements for Tourify, organized by track and release phase. See
[vision.md](vision.md) for the product thesis, the roadmap for sequencing, and
the milestones for checkable deliverables.

## Goal

Tourify is the intersection of a **music compendium** (artists, tours, and **venues** near
you) and a **social platform** (connections, stories, messaging) — it should feel like *both*.
Fans discover and get alerted to shows by bands they love, bands like them, at venues they
follow, and through the people in their scene — then coordinate going together. Organized
around three first-class nouns: **Artists · Venues · Friends**. North star of the compendium
pillar: strong **indie/long-tail** coverage (the MVP started mainstream to ship fast). It's a
**passion project, not for sale** — see [vision.md](vision.md).

Legend: ✅ done · 🔶 partly built · ⏳ planned.

---

# Compendium track (Phases 0–5)

## MVP (Phases 0–1) — ✅
- **Auth** — register/login/refresh (JWT).
- **Home location** — set location + radius (geocoded pick-list for disambiguation).
- **Artist search & follow** — find and follow bands; artist detail pages.
- **Event discovery** — upcoming shows by followed bands within radius (Ticketmaster).
- **Attendance** — mark a show `interested` / `going`; "Your shows" in My Music.

## Phase 2 — Recommendations, onboarding & enrichment — ✅
- **Similar bands near you** — Last.fm similarity (+ normalized-name bridge).
- **Spotify import** — connect Spotify to auto-follow top artists (onboarding only).
- **Artist enrichment** — links & merch (MusicBrainz + Spotify), bio + tags (Last.fm), plus
  **MBID verify/repair** and **romanized names** for non-Latin acts (TD-8).

## Phase 3 — Alerts — 🔶
- ✅ **In-app alerts** for matching shows (followed / similar near home) + per-type prefs.
- ✅ **`EmailSender` seam** (console in dev, SMTP in prod) — used by password reset.
- ⏳ **Native push** (Expo → APNs/FCM) + **live email delivery**.

## Phase 5 — Indie & own recommendations (north star) — ⏳
- **Own recommendation engine**, run side-by-side with Last.fm.
- **Indie event source** — *blocked:* Bandsintown shut down its public API; the multi-provider
  fan-out seam (`get_event_providers`) is ready for a replacement.

---

# Social track (co-pillar — Phases 4, 6–8)

## Phase 4 — Social graph — ✅
- **Friends** — invite links + add-by-email; requests / accept / decline / remove.
- **Friends going** — "N friends going" on events; attendance visibility (public/friends/
  private); friend-going alerts.
- **Feed & profiles** — Social tab with a recency-ordered activity feed; friend profiles (bio,
  top bands, going/interested); **mutual friends & bands**. Other users are exposed by display
  name + avatar only — never email.

## Account & profile — ✅
- **Password reset** — single-use hashed tokens, expiry, session invalidation (`token_version`).
- **Editable profile** — display name, bio, and uploaded **avatar**.

## Venues (first-class noun) — 🔶
- ✅ Follow venues; venue card (upcoming shows, follower count, friends who follow); "friends
  following" on artist pages; Venues section in My Music.
- ⏳ (Phase 6) venue profiles, venue-centric discovery, venue alerts, "your scene."

## Phase 6 — Connections, profiles, venues & the safety floor — ⏳
- **Venues-as-first-class** (profiles, discovery, alerts, "your scene"); rich **profiles**;
  the multi-signal **Friend Finder** (mutual friends + mutual/frequented venues + shared &
  similar taste).
- **Safety floor (gates everything public — TD-9):** public-first **tiered visibility**
  (identity/taste/attendance public by default; precise location never; per-item + global
  **private mode**) **and Block & report** (symmetric, enforced server-side on every social
  query). The public-attendance default must not flip on until these land.

## Phase 7 — Stories & moments — ⏳
- Short **video/image stories** tied to a show; a feed story tray. Introduces the media
  pipeline (object storage + CDN + transcoding) and ephemerality.

## Phase 8 — Messaging — ⏳
- **1:1 DMs + event group chats.** Introduces real-time delivery; respects blocks; DMs are
  private and never mined for discovery.

---

## Cross-cutting

- **Privacy & safety** — public-first but tiered (TD-9); **Block & report** is a prerequisite
  before public social opens beyond trusted testers.
- **UX rework** — streamline the IA around the three-noun, co-pillar experience: a blended
  home feed + social proof on every entity page (see the design notes).

## Non-goals (for now)

- No paid/subscription features, ticket sales/checkout, or artist-facing tools. **Not for
  sale.** Ambition is growing, but it stays a passion project — infra stays as simple as each
  phase allows (real-time + media land only with Phases 7–8).

## Success signals (portfolio context)

A clean, demoable flow that shows the **flywheel**: follow bands/venues → nearby + similar
shows → alert → see your scene / who's going → **go together** with a friend → (later) share
the moment.
