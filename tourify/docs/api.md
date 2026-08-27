# API

REST, JSON, client-agnostic. Auth via bearer JWT (access + refresh). All routes except
`/auth/*`, `/health*`, `/`, and the Spotify `/callback` require a bearer token.
✅ = built; ⏳ = planned.

## Health
```
GET  /                                 # name/version/docs
GET  /health
GET  /health/db                        # verifies DB reachability
```

## Auth & profile  ✅
```
POST  /auth/register                   -> { access_token, refresh_token }
POST  /auth/login                      -> { access_token, refresh_token }
POST  /auth/refresh                    # { refresh_token } -> new token pair
GET   /auth/me                         -> current user (incl. own email, bio, avatar_url)
PATCH /auth/me                         # { display_name?, bio? } partial update
POST  /auth/forgot-password            # { email } -> always 200 (no enumeration); dev returns reset_link
POST  /auth/reset-password             # { token, new_password } -> 204; bumps token_version (logs out all sessions)
POST   /me/avatar                      # multipart image (jpeg/png/webp ≤5MB) -> user w/ avatar_url
DELETE /me/avatar                      # clear avatar
```
Tokens embed a `ver` claim = `users.token_version`; a password reset bumps it, so every
outstanding access/refresh token stops validating. Avatars are served from `/media`.

## Artists  ✅
```
GET  /artists/search?q=&limit=         # Ticketmaster-backed search (upserts hits)
GET  /artists/{id}                     # detail; lazily fetches + caches links, bio, tags
GET  /artists/{id}/friends-following   # friends who follow this artist
```
`GET /artists/{id}` returns `links` (curated: website/bandcamp/socials/streaming — from
MusicBrainz URL rels + Spotify), `bio` (lead paragraph) + `tags` (Last.fm), and
`romanized_name` (Latin companion for non-Latin acts). First view lazily enriches:
bio/tags → MBID verify/repair (+ romanization) → links (see TD-7, TD-8).

## Location & geocoding  ✅
```
GET  /geocode?q=&limit=                # candidate places (Nominatim) for disambiguation
GET  /me/location
PUT  /me/location                      # { lat,lng,label } or { query } (geocoded) + radius_km
```

## Follows  ✅
```
GET    /me/artists                     # followed bands
POST   /me/artists/{id}                # follow (source=manual); triggers tour sync,
                                        # similarity refresh, alert eval
DELETE /me/artists/{id}                # unfollow
```

## Events, discovery & attendance  ✅
```
GET  /events?lat=&lng=&radius_km=&artist_id=&limit=   # nearby (defaults to home)
GET  /events/{id}
GET  /me/discovery                     # upcoming shows by bands you follow, near home
GET  /me/discovery/similar             # nearby shows by similar bands (Last.fm + name bridge)
GET  /me/discovery/venues              # upcoming shows at venues you follow (any location)
GET  /me/shows                         # your going/interested upcoming events (+status)
POST   /events/{id}/attendance         # { status: interested|going, visibility }
DELETE /events/{id}/attendance
GET    /me/attendance                  # raw attendance rows
GET    /events/{id}/friends-going       # friends going/interested (respects visibility)
```

## Venues  ✅
```
GET    /venues/{id}                     # venue card: details, upcoming shows, following,
                                        # follower_count, friends_following, regulars (top
                                        # public attendees; honors blocks + private mode)
GET    /me/venues                       # venues you follow
POST   /me/venues/{id}                  # follow venue
DELETE /me/venues/{id}                  # unfollow venue
```

## Safety — blocks & reports  ✅ (Phase 6a, TD-9)
```
GET    /me/blocks                       # users you've blocked
POST   /me/blocks/{user_id}             # block (removes any friendship; refuses new requests)
DELETE /me/blocks/{user_id}             # unblock
POST   /reports                         # { subject_type, subject_id, reason, note? } — capture-only
```
`PATCH /auth/me` also accepts `discoverable` (global private mode); `/me/notification-prefs`
gains `notify_venues`. Attendance defaults to `visibility: public` (per-item override kept).

## Notifications  ✅ (in-app)
```
GET   /me/notifications
GET   /me/notifications/unread-count   -> { count }
POST  /me/notifications/read-all
PATCH /me/notifications/{id}/read
GET   /me/notification-prefs           -> { notify_followed, notify_similar, notify_friends, notify_venues }
PUT   /me/notification-prefs
```

## Onboarding — Spotify import  ✅
```
GET  /onboarding/spotify/connect       # (authed) -> { authorize_url } with signed state
GET  /onboarding/spotify/callback      # (public) verify state, exchange code, import top
                                        # artists as follows (source=spotify_import); HTML page
```

## Social — friends  ✅ (Phase 4)
```
GET    /me/friends                     # accepted friends w/ mutual_friends + mutual_bands counts (no email)
GET    /me/friends/suggestions         # Friend Finder: people you may know + reason (blocks/private honored)
GET    /me/friends/{id}/profile        # friend profile: bio, top bands, going/interested, mutuals (friends-only)
GET    /me/friends/requests            # incoming pending requests
POST   /me/friends/requests            # { email } or { user_id } -> send request
POST   /me/friends/requests/{id}/accept | /decline
DELETE /me/friends/{id}                # remove friend
GET    /me/friends/activity            # recency-ordered feed of upcoming shows friends are attending
GET    /me/friends/invite              # your stable reusable invite code
POST   /me/friends/redeem              # { code } -> auto-accepted friendship (idempotent)
```
Other users are exposed as `{ id, display_name, avatar_url }` only — **never email**.

## Push channel  ⏳ (Phase 3 remainder)
```
POST   /me/push/register               # register Expo push token { token, platform, device_id }
DELETE /me/push/register
```

See also: [architecture.md](architecture.md), [database.md](database.md),
[backend.md](backend.md).
