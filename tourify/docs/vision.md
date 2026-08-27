# Vision

**Tourify lives at the intersection of two things that rarely coexist well: a robust music
compendium and a real social platform.** On one side, a reference-quality guide to live
music — the bands, the tours, and the **venues** near you. On the other, a genuine social
network — connections, stories, and messages — built around *going to shows*. Neither half is
new; **the intersection is the product.** Tourify should feel like *both* a music-exploration
app and a social app, because for live-music fans those are the same experience: you
discover shows through your people and your scene, and you build your people and your scene
by going to shows.

## The two pillars

- **The compendium — the utility spine.** A reference to live music organized around three
  first-class nouns: **Artists · Venues · Friends**. Follow bands *and* venues; see tours and
  local shows; know your scene. High-intent, and the reason to exist.
- **The social platform — the engagement engine.** Connections, profiles, an activity feed,
  stories/moments from shows, and messaging — all **anchored to music** (a story is from
  *this show*, a chat is around *this event*, a connection is via *shared bands or venues*).
  The reason to open the app on a random Tuesday.

The bet is that the intersection is a **flywheel**: discovery drives social (find a show →
invite → go together → share a moment), and social drives discovery (see what your scene
follows and attends → discover through them). **Venues are the connective tissue** — where
taste and people physically meet ("your local scene").

> **"Your scene" — the one-word thesis.** The scene is **where your people, your taste, and your
> venues align** — the intersection made personal. It is both the flywheel's *output* and its
> *fuel*: the shows where all three converge are the best recommendations **and** the moments that
> grow your graph. Surfacing your scene — the rooms you love, the people you keep running into
> there, and the shows where they meet — **is the point of the app.** (Named as the Phase 6e
> *Your scene* feed; the multi-signal **"Your scene"** rail on Discover is its first concrete
> expression — a show tagged *your band · friends going · venue you follow* is literally your
> scene aligning.)

> **Guardrail — the intersection is the product, not the sum.** The failure mode is bolting a
> generic chat app onto a concert search and doing neither well. So: *every social feature is
> music-anchored, and every exploration surface is social.* Not chat plus a separate event list.

## Signature experiences — the "only-here" moments

Three experiences exist *only because* Tourify is both pillars. They're the soul of the app:

1. **Going together.** From any show, one tap to invite people or start a group; the plan
   lives *on the event* — who's in, where to meet. Discovery → coordination → attendance → the
   shared memory. *(Needs both the show data and the graph.)*
2. **Your scene.** A living feed fusing the people, venues, and bands you follow: "3 of your
   people are going to X," "your venue announced Y," "someone near you who loves your bands is
   going to Z." *(Fuses the compendium with social activity.)*
3. **The venue as home base.** A venue isn't a line on a ticket — it's a community: its shows,
   its regulars, your friends there, the local scene. You **belong to rooms**, not just follow
   bands. *(A venue is a data entity and a social hub.)*

**Stories/moments** from shows layer on top later (Phase 7) as the live emotional hook — feel
your scene's energy in real time.

## Core loops — the flywheel in motion

Tourify runs **two loops that share one turbine.** Neither pillar spins this alone.

- **The Compendium loop — the retention *floor* (low-frequency, high-intent).**
  `follow bands/venues → shows surface near you → mark going/interested → attend → taste
  deepens → better shows surface.` Works at N=1, needs no friends; the reason you install and
  don't churn.
- **The Scene loop — the engagement *ceiling* (high-frequency, habitual).**
  `open → your scene → react / connect / coordinate → go together → share → your activity
  feeds everyone else's scene.` The habitual, daily open.

**The turbine — "going" is public.** In a compendium-only app, "going" is a private bookmark;
here it's a public signal, and that couples the loops: every commit *emits* social fuel (you
appear in friends' feeds and on a venue's "who's going"), and every glance at your scene *is*
discovery (you find shows through people, not just your own follows). North-star kicker: **your
scene surfaces indie/long-tail shows an algorithm never would** — a friend going to a tiny DIY
show *is* the recommendation.

**"Your scene" is an adaptive priority stack** — which is also how graceful emptiness works. It
fills in as the graph grows and is never a dead screen:

| Graph state | Your scene is mostly… |
|---|---|
| N=1 (no connections) | geography + taste — nearby shows, similar bands, local venues |
| following venues | + the rooms you follow and their activity |
| connected | + your people's activity, which grows to dominate |

**Growth loop.** Going-together is viral by nature (concerts are social — you bring people):
`invite / start a group → they join → public attendance + stories pull more in → bigger graph
→ richer scene`.

**In one line:** the compendium keeps you from churning; the social gets you back today; and
public "going" turns every utility action into social fuel and every social glance into
discovery.

## Origin & north star

The idea came from the frustration of tracking **indie band tours** — acts that don't get
algorithmic push and whose shows are easy to miss. Maximizing **indie/long-tail coverage**
remains a north star of the compendium pillar. The MVP deliberately started with mainstream
data (clean, free, no-approval) to ship something verifiable fast, with provider seams so
indie sources slot in behind the same interface.

## What it does (and will do)

- **Follow your bands and venues** — search and follow artists and rooms; import top artists
  from Spotify to skip the cold start.
- **Shows near you** — upcoming concerts by followed bands and at followed venues, within your
  radius; plus nearby shows by *similar* artists.
- **Know your scene** — venue profiles, which of your people follow/attend, your local
  regulars.
- **Get alerted** — push the moment a matching show (band, venue, or friend) appears.
- **Connect & coordinate** — add connections, see who's going, message and plan, and (later)
  share stories/moments from shows.

## Product principles

- **The intersection is the product.** Social features are music-anchored; exploration
  surfaces are social (see the guardrail above).
- **Three nouns.** Artists · Venues · Friends — each followable, each with a profile, each
  surfacing social proof and interconnecting. *(We may rename "Friends" → "Connections" as the
  social graph broadens beyond mutual accept.)*
- **Mobile + push is the experience.** Native (Expo), push as a first-class channel — now for
  shows, later for social.
- **Relevance over volume.** Surface the right five shows (and the right few people), not a
  flood.
- **Grow the graph honestly.** Social bootstraps via invite links and shared interest
  (bands / venues / scene), never borrowed third-party friend lists.

## The graph & privacy

Two structural decisions shape the social pillar. *(How it works at any scale — a
solo-valuable compendium plus a scene that "fills in" — lives in **Core loops** above.)*

**Connections:** **friends-first** (symmetric, the intimate core) now; **asymmetric *follow***
(tastemakers, curators, scene voices) later — an extension of how you already follow Artists
and Venues.

**Privacy — public-first, but tiered.** We go **public by default (opt-out)** so the graph can
bootstrap *before your friends join* — scene discovery and the Friend Finder surface real
people from day one, and a venue shows who's going, not just your friends. But it's tiered to
protect real-world safety: **discoverable identity, protected whereabouts.**

| Public by default (opt-out) | Never public / user-controlled |
|---|---|
| Name, avatar, bio; followed bands/venues; **going/interested**; coarse city/scene | **Precise/home location** (never); any attendance a user marks friends-only/private |

Public "who's going" is powerful *and* sensitive, so safety is **first-class scope, not
polish**:

- **Precise location is never public** — a show's venue is inherently public; *your* home and
  exact whereabouts are not.
- **Per-item + global control** — any attendance can be flipped friends-only/private (the
  mechanism exists), plus a global **private mode**. Public is a default, never a trap.
- **Block & report is a hard prerequisite** — a block is symmetric and enforced
  **server-side on every social query**, never UI-only. (See TD-9.)

At scale this stays a Postgres/PostGIS graph — read-time feeds + batch counts today,
fan-out / denormalized counters when it grows.


## Scope & intent

Tourify is a **passion project and portfolio piece** with **growing ambition** — but
deliberately **not for sale**: no subscriptions, no ad model, no selling out. That keeps
decisions biased toward free public APIs, a clean modular monolith, and demoable quality.
Going co-pillar *does* raise the technical bar over time — real-time delivery, a media
pipeline for stories, and moderation all become real — so the social pillar is **sequenced
into committed phases** rather than shipped at once (see the roadmap). Writing
our own recommendation engine remains an explicit goal.

## Personas

Casual Fan · Dedicated Fan · Music Tourist · Collector · **Scene Regular** — see
[personas.md](personas.md).

[user-stories.md](user-stories.md), [prd.md](prd.md), [architecture.md](architecture.md).


---

*Excerpted. Sections on competitive positioning and the unshipped roadmap are omitted.*
