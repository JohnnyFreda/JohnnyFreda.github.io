# Frontend

**Expo (React Native), single codebase** → iOS + Android + web (react-native-web).
Expo Router, strict TypeScript, **NativeWind** styling, dark "gig-poster" theme. The
FastAPI API is client-agnostic, so the same backend serves all surfaces. Mobile + push is
an explicit goal (native push is the Phase-3 remainder; the in-app inbox ships now).

## Structure

```
app/
  app/                         # Expo Router routes
    _layout.tsx                # AuthProvider + route guard (redirects to /login)
    login.tsx                  # login / create account (password show-hide toggle)
    notifications.tsx          # alerts inbox (marks all read on open)
    artist/[id].tsx            # artist detail: image, follow, tags, bio, links & merch
    (tabs)/
      _layout.tsx              # 4 tabs + header (bell + hero-badge account menu)
      index.tsx                # Discover — "Your bands" + "Similar to you" (EventGrid)
      search.tsx               # artist search + follow
      my-music.tsx             # Upcoming shows + Following (unfollow)
      you.tsx                  # profile, home location (pick-list), notif prefs, Spotify import
  src/
    lib/         api.ts (typed client), auth.tsx (context + guard), tokenStore.ts, format.ts
    components/  ui (Button/TextField/Card), EventCard, EventGrid, ArtistRow, EmptyState
    theme/       tokens.ts
  assets/        icon/splash/favicon + logo/iconhero/hero
```

## Navigation & chrome

- **Bottom tabs:** Discover · Search · My Music · You (tab bar accounts for safe-area).
- **Header (all tabs):** a **notifications bell** (unread badge, polls every 15s) → the
  inbox, and a **hero-badge** that opens the account menu (Log out).
- **Auth gate:** `useProtectedRoute` redirects to `/login` when signed out. Tokens in
  SecureStore (native) / localStorage (web); the API client auto-refreshes on 401.
- **Cross-tab freshness:** list screens refetch on focus (`useFocusEffect`) so
  follow/attendance/unfollow stay in sync across components.

## Layout notes

- **Responsive grid** (`EventGrid`): event cards flow into 3 / 2 / 1 columns by window
  width; card images use a 16:9 aspect ratio.
- Themed scrollbars on web; lists are touch/finger-scrollable.

## Notifications

In-app inbox now (bell + `notifications.tsx`). Native push (Expo Notifications →
APNs/FCM) + device-token registration are the Phase-3 remainder; they slot in as another
delivery channel without changing the alert pipeline.

## Tooling

Expo (managed) + Expo Router, NativeWind, strict TS. EAS Build for native binaries.
Design language in [ui-ux.md](ui-ux.md); conventions in
[coding-standards.md](coding-standards.md).
