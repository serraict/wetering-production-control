# 1. Zulip-backed per-lot messaging

Date: 2026-05-18

## Status

Accepted.

## Context

Operators, growers, and planners need a place to discuss a specific
production lot from inside the app. Today those conversations live in
WhatsApp, e-mail, and hallway chats and are lost from the lot's history.

Wetering already runs Zulip (`zulip.${VINE_ENVIRONMENT}.serraict.me`) as
team chat. Zulip's stream/topic model maps cleanly onto our domain: one
topic per lot inside a dedicated stream, so we can lean on an existing tool
instead of building our own conversation store.

Constraints when this ADR was written:

- The app has no user-facing login of its own; identity is established at
  the reverse proxy by Authelia, which injects `remote-name` / `remote-email`
  headers (`src/production_control/web/auth.py:6`).
- We have no per-user Zulip identity available to the app, only a shared
  bot account.
- The entry point for the feature is `/scan/view/{id}`, a mobile-optimised
  view where lot details are already rendered. Adding a "Communicatie" card
  there is the cheapest way to make conversation visible from the lot.

## Decision

1. **Backend.** Use the existing Zulip server as the message store. The app
   does not persist messages locally and has no inbox/notification of its
   own.
2. **Stream and topic mapping.** All conversations live in the `teelt`
   stream (configurable via `ZULIP_STREAM`). The topic name is the lot's
   numeric `id` rendered as a string — deterministic, never derived from
   mutable fields, no mapping table in our database.
3. **Identity.** The app authenticates to Zulip with a single shared bot
   account (`ZULIP_BOT_EMAIL` / `ZULIP_BOT_API_KEY`). The bot is therefore
   the `sender` of every message that originates from the app.
4. **Authorship convention.** When the app posts on behalf of a logged-in
   user, the service prepends `**{user_name}**: ` to the message body, with
   `user_name` taken from `get_current_user()`. On read, the service strips
   the same prefix and exposes a parsed `author_name` and `body_html` on
   each message. The chat UI uses the parsed `author_name` as the speaker
   label and aligns a bubble to the right (`sent=True`) when it matches the
   current user.
5. **Module shape.** The integration lives in `production_control.zulip_chat`
   behind a small service interface (`get_messages`, `post`, `narrow_url`)
   that returns plain dataclasses. The web layer never imports the Zulip
   SDK. Configuration follows the existing `OPCConfigManager` pattern.
6. **Failure mode.** Any Zulip error surfaces as a `ZulipServiceError` and
   is caught by the UI; the rest of the page continues to render.
7. **No realtime in v1.** No long-poll or event-queue subscription; the
   card has an explicit refresh button and re-fetches after each post.

## Consequences

### Good

- Zero new persistence to design, back up, or migrate. Conversations
  outlive any single deployment of `production_control`.
- The same topic is reachable from native Zulip clients (mobile, desktop,
  web) — discussions started in-app continue elsewhere without bridging.
- The deterministic topic name (`str(lot.id)`) means the integration is
  stateless from our side: any process that knows the lot id can find the
  topic.
- The service interface keeps the rest of the codebase decoupled from the
  Zulip SDK; the same `get_messages(lot)` / `post(lot, content)` can later
  back other entry points (inspectie, detail pages) without rewiring.
- The `**name**: ` prefix convention is portable: messages posted to the
  same topic from a native Zulip client still display sensibly in the app
  (they fall back to Zulip's `sender_full_name`).

### Bad / accepted trade-offs

- **Spoofable authorship.** The human author is a string prefix in the
  message body, not a cryptographic identity. A user with access to the
  form can post `**Someone Else**: ...` and we will display it that way.
  The bot's account is the only authentication; the inline name is a
  convention. This is acceptable for an internal tool behind Authelia and
  is documented for future re-evaluation.
- **One Zulip identity for everyone.** Notifications, mentions, and direct
  replies in Zulip target the bot, not the human. Users who want to react
  or follow up natively in Zulip lose the per-user context.
- **No realtime updates.** Users must click "Vernieuwen" or post a message
  to see new content. Acceptable for the scan view's intermittent-use
  pattern; a follow-up could subscribe to Zulip's event queue.
- **Bot-account rate limits and outage exposure.** A Zulip outage or a
  rate-limited bot blocks all in-app messaging at once; mitigated by the
  card degrading to an inline error and the rest of the page rendering
  normally.
- **String-matching alignment.** The `sent=True` decision is exact string
  equality between Authelia's `remote-name` and the prefix the user posted
  earlier. If the display name changes, old bubbles stop aligning to the
  right. Considered cosmetic.
- **Topic name is opaque in Zulip.** A bare `"12345"` topic shows no
  context to someone browsing the stream directly; they need to look the
  lot up in production_control. Trade-off accepted in exchange for
  permanently-stable topic names.

## Future work / triggers for revisiting

- If we add a real per-user login (OAuth to Zulip, or another IdP), revisit
  decisions 3 and 4 to get authenticated authorship.
- If multi-tab or multi-device "see new messages without refreshing" becomes
  a felt need, add a Zulip event-queue subscription per page session.
- If the conversation surface expands beyond `/scan/view/{id}` to many
  pages, evaluate whether a shared "open conversation drawer" component
  beats per-page cards.
