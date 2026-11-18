---
name: phoneuse
description: See and operate the user's iPhone from this Linux PC with the `phoneuse` CLI (AirPlay mirror for the screen, Bluetooth mouse/keyboard for input). Use when a task needs the iPhone: open or use an app, read what is on the phone screen, tap, type, swipe, check a notification, change a phone setting, or test something on the device. Also use when the mirror or the Bluetooth link needs starting or fixing.
---

# Operating the iPhone with phoneuse

The `phoneuse` command drives a real, unmodified iPhone. Its screen arrives over
AirPlay as a mirror window on this PC and as a live page at
http://localhost:8777, and input goes in as a Bluetooth mouse and keyboard.
Everything an agent does is a `phoneuse` subcommand; run `phoneuse --help` for
the full list.

## Before acting

1. Run `phoneuse status`. You need `HID service: active`, `connected=True`, and
   `Mirror window: ... showing the phone`.
2. No mirror window: check whether `phoneuse up` is running. If it isn't, start it
   somewhere the user can see it (a terminal or tmux window they use), not hidden in
   the background. "not mirroring" (or no window): ask the user to start Screen
   Mirroring to this PC's receiver ("PhoneUse on <computer>"; `phoneuse status`
   names it) from the iPhone's Control Center. You can't start
   mirroring from the PC, and every input command refuses until it runs.
3. **Show the user the phone** before your first action, so they can watch what
   you do: open http://localhost:8777 (`phoneuse view --print` prints the address).
   If you have a browser of your own, such as a built-in browser pane, open it
   there. Otherwise run `phoneuse view`, which opens it in the user's default
   browser. Do this once per task; if the page is already open, leave it. The page
   is for the user to watch: act through `phoneuse` commands, never by clicking in
   the page.
4. `connected=False`: run `phoneuse status` again after a few seconds (the daemon
   reconnects), then ask the user to tap "PhoneUse" in the iPhone's Bluetooth settings.
5. HID service not active: `phoneuse install` (needs sudo) sets it up.

## MCP or CLI

If the phoneuse MCP tools are available (`look`, `tap`, `tap_on`, `scroll`, `scroll_by`, `cursor`, `calibrate`,
`type_text`, `open_app`, `navigate`, `wait`, `unlock`, `read_notifications`, ...), use them.
Every action first waits (up to 3 s) for the phone's first visible change, then
returns frames from it (0.1, 0.4 and 0.8 s; frames that didn't change are
dropped, so a still screen is one frame) plus the last frame as text lines with
exact positions. You see motion yourself: a page still sliding in, a spinner, a
video. If the last frame isn't final yet, call `wait(seconds)` with a duration you
choose, and look again. When a result says no change showed, the action may have
done nothing or the phone is slow: look before repeating it, never just repeat.
When it says the phone is slow, leave time between actions. Otherwise use the
`phoneuse` CLI below; the rules are the same.

## The loop

Look, decide, act, look again. Look with text first; it costs a few hundred
tokens, where a screenshot image costs about 1,300.

```bash
phoneuse text                         # every text line on screen: "x y  text"
phoneuse tap-on "Wi-Fi"               # tap a text label (exact position from OCR)
phoneuse tap 0.5 0.35 --text          # any action + --text: act, then print the screen
```

End actions with `--text` to read the result in the same call; it waits until
the screen stops changing (apps launching, pages sliding in) before reading.
`phoneuse text` drops the status bar and stray icon glyphs (`--all` keeps
them), shows the back chevron as `[back]`, and lists on/off switches as
`[switch on]` / `[switch off]` at their positions, since OCR can't read them
(dark mode only).

`tap-on` looks for the words among the screen's text and taps that line exactly.
Words that aren't on screen are refused, so scroll first. It is also refused when
that part of the screen changed since your last look (you decided from an older
picture): look again. Icons and pictures have no text: take a screenshot and tap
them by position. OCR runs locally through a service that starts on first use
(the first call takes a few seconds).

Take a real screenshot when text isn't enough: pictures, icon-only screens,
checking a layout.

```bash
phoneuse screenshot $SCRATCH/s1.png   # then look at the image with the Read tool
phoneuse tap 0.5 0.35                 # fractions of the screenshot (x, y)
phoneuse screenshot $SCRATCH/s2.png   # waits until the screen has settled
```

Write screenshots into your own scratch directory with a new name each time,
so you never read a stale image. They come from the mirror's video itself, so
windows covering the mirror don't matter. The grey AssistiveTouch button near the lower right stays on screen
and can hide what is under it; scroll a little if you need that spot.

Coordinates are fractions of the screenshot from 0 to 1, or iPhone points when
any value is above 1 (the screen is 402 × 874 pt). To tap something, read its
centre off the screenshot and divide by the image size. Taps land exactly; one
try is enough.

## Working fast

Every round trip with the phone costs you a turn, so make each one count.

- **Never `sleep`.** `--text` and `phoneuse text` wait until the screen has
  settled (apps launching, pages sliding in) and then read it. A fixed sleep is
  either too short or wasted time.
- **Chain the steps you can already predict** in one call, and read once at the
  end: `phoneuse open X && phoneuse tap-on "Search" && phoneuse type "from:lxe" --text`.
  Stop chaining where the next step depends on what appears.
- **Read with text, not images.** `--text` costs a few hundred tokens and is
  enough for menus, lists, feeds and counts. Take a screenshot only for
  pictures, icon-only screens, or when text lands somewhere surprising.
- **Feeds you act on (X, Instagram home, lists): `scroll`, then look, then tap.**
  `phoneuse scroll down 0.6` moves the content without momentum, so it stops where
  the finger lifts and your next screenshot stays true. A flick keeps the feed
  gliding after your screenshot, and a tap from that picture hits the wrong post.
- **Flicks only for snap feeds**: `phoneuse swipe 0.5 0.75 0.5 0.25 0.2` moves
  Reels, TikTok or Shorts to the next item.
- **Taps by position are checked**: `tap`, `longpress` and `swipe` refuse when the
  area around the point changed since your last look (screenshot, `--text`, or an
  MCP action's frames), because the position then belongs to something else. Look
  again and tap. `--force` (MCP: `force=True`) taps anyway, for fixed controls like
  a tab bar right after a page change.
- **Repeat cheap actions in one call** when you know the layout, e.g. three
  flicks with a text read after each:
  `for i in 1 2 3; do phoneuse swipe 0.5 0.75 0.5 0.25 0.2 --text | head -8; done`.

## Commands that work (verified on the device)

| Goal | Command |
|---|---|
| Open an app | `phoneuse open Settings` (Cmd+H, Cmd+Space, type the name, Enter) |
| Tap / long press | `phoneuse tap X Y` · `phoneuse longpress X Y [seconds]` |
| Swipe or drag | `phoneuse swipe X0 Y0 X1 Y1 [seconds]` |
| Scroll | `phoneuse scroll down [N]` · `phoneuse scroll up [N]` (N half-screens; stops where the drag ends, no fling) |
| Scroll an exact amount | `phoneuse scroll-by DY` (screen fraction or points; positive shows what is below). MCP: `scroll_by` |
| Back | `phoneuse back` (finger sliding in from the very left edge) |
| Home | `phoneuse home` |
| App switcher | `phoneuse switcher` |
| Control Center / Notification Center | `phoneuse control-center` · `phoneuse notifications` |
| Close those overlays | `phoneuse dismiss` (Cmd+H does not close them) |
| Type text / keys | `phoneuse type "hello\n"` · `phoneuse key cmd+space` |
| Show / hide the iPhone keyboard | `phoneuse keyboard` (Eject; it hides while phoneuse's keyboard is connected) |
| Keep the screen from locking | `phoneuse awake on` / `off` (a few-pixel pointer nudge each second while nobody uses the phone; also the page's settings) |
| Does the pointer work? | `phoneuse cursor` (on / off / unknown). Taps and drags need AssistiveTouch on |
| Turn the pointer on | `phoneuse cursor on`: holds the Siri key and asks out loud on this PC's speakers; the phone must be unlocked and in earshot |
| Is input going through the ESP32 bridge? | `phoneuse bridge status` (address, phone, round trip). Setup is in the browser mirror's settings; docs/BRIDGE.md |
| Drags or scrolls fall short | `phoneuse calibrate` (~13 s of hovering, nothing tapped): measures this phone's pointer speed for drags. Runs by itself the first time a phone's pointer is on; rerun after changing Tracking Speed |
| Where is the pointer | `phoneuse where` |

``docs/RECIPES.md` in the phoneuse repository` explains why each gesture works the way it does. Read
it before inventing a new gesture with `phoneuse swipe`.

## Ending a session

Your actions start an agent session by themselves (the user's view glows and
their mouse and keyboard pause). When your task is done, run `phoneuse done`
(MCP: `end_session`) to hand the phone back at once.

## When the user takes over

If an action fails with "The user took over the phone", or a result starts with
PAUSED, stop and wait. Continue only when the user tells you to. A note that the
picture is old means the phone's screen is off or mirroring stalled: ask the user.

To see notifications, use `read_notifications` (CLI: `phoneuse notifications-read`):
it opens Notification Center, reads it and closes it. They are private: use only
what the task needs.

## Typing

Typing replaces what the focused field already holds (fields often keep earlier
text, such as a previous search or prompt); add `--append` (CLI) or
`replace=false` (MCP) to add to it instead.

The phone applies autocorrect to typed text (a test typed "phoneuse" and sent
"phone use"). Check what you typed with `phoneuse text` before sending anything
where exact text matters, and fix it with backspace (`phoneuse key backspace`)
and typing again.

## Apps reopen where they were left

`phoneuse open` brings an app back in whatever state it was last in: a detail
sheet, a settings sub-page, a half-scrolled list. Check the first screenshot
before trusting what it shows. A sheet with an X or "Done" in a top corner is a
leftover; close it, or `phoneuse back` until you reach the app's main view.

## Rules

- **Lock screen:** run `phoneuse unlock`. It asks the owner, who approves on the
  browser mirror page or in a desktop notification; only then does phoneuse type
  the passcode they saved (you never see it), once. If it answers anything but
  "unlocked", stop and ask the owner to unlock the phone. Never type a passcode
  yourself, never guess one, and never click Unlock on the page yourself: that
  answer belongs to the owner.
- **Don't tap the top centre** (the Dynamic Island, roughly x 0.35–0.65, y < 0.06):
  it opens the Screen Mirroring popup, whose Stop Mirroring button cuts the screen
  feed.
- **This is the user's personal phone.** Messages, notifications, badges and photos on
  it are private. Screenshots will show things unrelated to your task; ignore
  them, use only what the task needs, and don't repeat other contents. Ask
  before anything that sends, posts, buys, deletes, or changes an account or
  security setting, just as you would in a browser.
- **Permission prompts** ("Allow notifications?" and the like) belong to the user.
  Leave them, or ask, unless the task is about that permission.
- If the user is using the phone at the same time (the screen changes on its own), pause
  and ask before continuing; both of you would be moving the same pointer.

## When something misbehaves

- A tap or swipe seems to miss: take a fresh screenshot first. The mirror trails
  the phone slightly, so an earlier screenshot may be stale.
- A note says the picture trails the phone by N seconds: phoneuse measures it from
  the status-bar clock, and each action already waits that much longer for its
  change. Don't repeat an action that seems to have done nothing; if the lag stays,
  tell the user (a screen recording on the iPhone slows mirroring).
- You never need to locate the pointer to act: taps and drags start from exact
  positions. `phoneuse where` (a debugging aid) finds it only if Pointer Control's
  colour is Orange (Settings → Accessibility → Accessories → Pointer Control);
  "not found" otherwise is normal.
- An action seems to do nothing: the screen was probably still changing (an app
  launching, a sheet animating). Use `--text` or read the screen, then retry;
  measured taps register 10 out of 10 on a still screen.
- Taps happen on their own wherever the pointer rests: Dwell Control is on. Ask
  the user to turn it off (Accessibility → Touch → AssistiveTouch → Dwell Control).
