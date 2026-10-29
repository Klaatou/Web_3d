# Joining a presence server: a note for creators

*29/10/2026. For the creator of a region who wants to connect it to a host's presence server. The host's side is in manual § 34 and procedures § 6, item 7.*

## 1. What this is

A presence server relays the positions, the chat and the visitor counters of a region. A host can welcome your page: your region stays hosted wherever you like (your own server, GitHub Pages...), only the presence server is on the host's side. The host decides who connects: each declared page only has access to its own rooms.

## 2. What you give the host

- **Your page's origin**: the start of its address, without a path, for example `https://alice.example` (with the port if it is not the usual one). If your page can be reached with and without `www`, give both.
- **A short identifier**, for example `alice`: it becomes your room prefix.
- A page opened from disk, and the viewer, have the origin `null`: the host decides whether to accept it.

## 3. What the host gives you

- **The server address**, as `wss://` (for example `wss://MACHINE.TAILNET.ts.net`). A page served over https can only reach a `wss://` server.
- **Your prefix**: your rooms are named `alice.NAME` (the case of the prefix is ignored).
- **Your limits**, if any: `maxWalkers` (walkers at the same time, all rooms together) and `maxRooms` (rooms open at the same time). The server's general limits apply too.

## 4. Setting up your page

Two ways, your choice:

- when building: `--presence-url wss://MACHINE.TAILNET.ts.net --room alice.galerie`;
- or in `NOM.config.json`: the keys `presenceUrl` and `room`.

`room` is not optional: without it, the room takes the page's name, which does not start with your prefix, and the server refuses. Then reload the page.

## 5. If presence is refused

The page shows "presence refused:" followed by the reason, and does not retry: reload it once fixed. "Copy diagnostics" (I key) shows the code 4003.

| Message shown | Cause | Who fixes it |
|---|---|---|
| this page is not declared on this presence server | your page's origin is not in the host's file (typo, `www`, port) | the host, or you if the origin you gave was wrong |
| the creator of this page is suspended on this presence server | your access is suspended | the host |
| this page's room does not belong to its creator on this server | `room` does not start with your prefix | you |
| its creator already has all allowed rooms open | `maxRooms` reached | you or the host |
| room full | no more room for walkers (`maxWalkers` or a server limit) | nobody: wait |

## 6. Visit log

The host can give you a key for your room (`visits-key alice.galerie` in their console). You then open your page's address followed by `#visits`, from any device, and type the key: visits per day, durations, CSV export. The log never contains an IP address. Details: manual § 31.

## 7. What the server records

- **The server log** (`--log`): one line per event, with the room, the nickname and **the text of every chat message**. The IP address is hidden by default (`--log-ip hash`), in clear with `--log-ip raw`, absent with `--log-ip none`. Retention: `--log-days` (30 days by default, `0` = no limit).
- **The chat history** (`--history-file`): nickname, text, room and time, never an IP address. The last 200 messages of a room are replayed to newcomers (`--history`). Retention: `--history-days` (30 days by default, `0` = no limit).
- **The visit log** (`--visits`): room, arrival, duration, walk time, browser fingerprint; never an IP address; the nickname only with `--visits-names`. Retention: `--visits-days` (365 days by default).
- **The nickname registry**: each browser has a random key; the first one to take a nickname keeps it, the following ones get `NAME#CODE`.

IP addresses, nicknames and messages are personal data: plan to inform your visitors. The exact rule depends on the country, check it on your side.

**Klaatou's demo server (as of 29/10/2026)**: IP addresses in clear (`--log-ip raw`), log and chat history kept without a time limit (`--log-days 0`, `--history-days 0`). This choice may change: ask the host.

## 8. What you do not control

- Moderation: the host reads the log and can kick or ban a visitor (`ejecter`, `bannir`).
- The suspension of your access, your limits, the retention period.
- The availability of the server: if it stops, your page gives up connecting after a few attempts and asks to be reloaded (manual § 36.4).

## 9. Tried, not tried

- **Tried** (29/10/2026): a page hosted on `https://NOMDUSITE.github.io`, its origin declared in the creators file of Klaatou's server, `wss://` provided by Tailscale Funnel (procedures § 11); an outside visitor walked there.
- **Not tried**: an outside creator's page on their own domain, Windows, Edge.
