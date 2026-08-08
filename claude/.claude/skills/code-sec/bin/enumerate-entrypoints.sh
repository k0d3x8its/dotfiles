#!/usr/bin/env bash
#
# enumerate-entrypoints.sh — list a codebase's network entry points.
#
# Shared deterministic core for the security suite: code-sec consumes this for
# its attack-surface inventory, bounty-hunter for the reachability-gate input.
# A silent miss here is dangerous, so the enumerator is scripted + test-backed
# rather than hand-enumerated per sweep, and it leans toward over-reporting: a
# spurious row is pruned by the reachability prompt, a missed one is invisible.
#
# Usage:  enumerate-entrypoints.sh <path> [path ...]
#
# Emits one pipe-delimited row per entry point:
#
#     file:line | kind | detail | exposure
#
#   kind      http-route | ws-handler | listener | contract-fn
#   detail    the trimmed source line (route path / handler / listen call)
#   exposure  public | local | internal | unknown  (file-level bind guess)
#
# Exposure is a FILE property (the bind host on the listen/run call), applied to
# every entry point in that file. It is a GUESS to seed the reachability prompt,
# never ground truth — deployment topology is confirmed by the user.
#
# Known blind spots (documented, not silent): class-based handlers whose routes
# are method names (Tornado `def get(self)`) surface only via their listener
# line; a Solidity signature whose visibility keyword wraps onto the next line is
# missed. Both risk large false-positive floods if matched by line regex.

set -uo pipefail

if [ "$#" -eq 0 ]; then
  echo "usage: $(basename "$0") <path> [path ...]" >&2
  exit 2
fi

# A mistyped target must not read as "no attack surface" — fail loud, distinct code.
for p in "$@"; do
  if [ ! -e "$p" ]; then
    echo "error: no such path: $p" >&2
    exit 2
  fi
done

# --- source-file discovery ---------------------------------------------------
# Always pass explicit paths to the search — a bare recursive grep with no path
# blocks on stdin in a non-tty shell.
find_sources() {
  find "$@" -type f \
    \( -name '*.py' -o -name '*.js' -o -name '*.mjs' -o -name '*.cjs' \
       -o -name '*.jsx' -o -name '*.ts' -o -name '*.tsx' \
       -o -name '*.go' -o -name '*.lua' -o -name '*.sol' \
       -o -name '*.ino' -o -name '*.cpp' -o -name '*.cc' -o -name '*.cxx' \
       -o -name '*.c' -o -name '*.h' -o -name '*.hpp' -o -name '*.hh' \) 2>/dev/null
}

# --- exposure guess ----------------------------------------------------------
# Strongest signal wins: an explicit public bind outranks a localhost one.
# `"::"` / `[::]` is the IPv6 all-interfaces bind (internet-facing); `::1` is
# IPv6 loopback and is handled by the local branch below.
detect_exposure() {
  local f=$1
  # A deployed contract is globally callable — every public/external function
  # is on-chain-reachable, so a .sol file's exposure is public by construction.
  case $f in *.sol) echo public; return ;; esac
  # An Arduino sketch running a WiFi/Ethernet server is reachable by anything that
  # can route to the device — no 0.0.0.0 literal to key on, so treat .ino as public.
  case $f in *.ino) echo public; return ;; esac
  if grep -qE '0\.0\.0\.0|ListenAndServe\(":|INADDR_ANY|"::"|\[::\]' "$f"; then
    echo public
  elif grep -qE '127\.0\.0\.1|localhost|::1' "$f"; then
    echo local
  elif grep -qE 'AF_UNIX|unix:|\.sock\b|NamedPipe' "$f"; then
    echo internal
  else
    echo unknown
  fi
}

# --- entry-point patterns ----------------------------------------------------
# Keep these SHAPE-based (decorator / method-call forms), not endpoint-name
# specific, so a new framework on a known form is caught for free.
#
# Receiver whitelist for the verb-call form (HTTP_VERB_RE) is broad but not
# open: it covers the common router/app handles (incl. single-letter `r`/`e`
# used by gin/chi/echo/fastify) WITHOUT matching HTTP *client* calls like
# `requests.get(` / `axios.get(` whose receivers are off-list. That boundary is
# the false-positive control — widen it only with a matching test.
RECV='(app|application|router|rtr|rt|r|e|mux|srv|server|api|fastify|http|web|bp|blueprint)'

# Case-SENSITIVE: decorators (Flask/FastAPI/NestJS), framework registration
# calls (aiohttp add_*, Flask add_url_rule), Go HandleFunc, lua `:verb(`.
HTTP_RE="@[A-Za-z_][A-Za-z0-9_]*\.(route|get|post|put|delete|patch|head|options)\(|@(Get|Post|Put|Delete|Patch|All|Options|Head)\(|\.(add_get|add_post|add_put|add_delete|add_route|add_url_rule)\(|\.HandleFunc\(|:(get|post|put|delete|match)\("
# Case-INSENSITIVE (run separately): receiver.verb( — catches gin r.GET, chi
# r.Get, echo e.GET, fastify fastify.get, mixed case across Go frameworks.
HTTP_VERB_RE="\b${RECV}\.(get|post|put|delete|patch|all|head|options)\("

WS_RE='@[A-Za-z_][A-Za-z0-9_]*\.on\(|\b(io|wss?|socket)\.on\(|\.on\((["'\''])connection\2'

# Listeners: server-run receivers (incl. gin r.Run / aiohttp web.run_app / echo
# e.Start), generic listen/serve, and a socket bind QUALIFIED to a tuple / port
# / host literal so `fn.bind(this)` and `.bind(null, …)` don't masquerade as
# network binds.
LISTEN_RE='\b(app|application|socketio|server|srv|uvicorn|http|web|r|router|api|e)\.(run|Run|run_app|Start)\(|\.(listen|Listen|ListenAndServe|serve|Serve)\(|net\.Listen\(|\.bind\((\(|[0-9"'\''])'

# Solidity: externally-callable functions are the on-chain attack surface.
# Matches `function f(...) external|public` and receive/fallback. Assumes the
# visibility keyword sits on the signature line (common style); a wrapped
# signature is the documented blind spot above.
SOL_RE='function[[:space:]]+[A-Za-z_][A-Za-z0-9_]*[^;{]*\b(external|public)\b|\b(receive|fallback)[[:space:]]*\([[:space:]]*\)'

# Arduino/ESP (C/C++): a WiFi/Ethernet web server is the device's network surface.
# Route form is `server.on("/path", handler)` — the leading-slash string arg
# distinguishes an ESP HTTP route from a WebSocket `.on("connection")` (WS_RE).
# Listener signal is the server-object DECLARATION (type followed by a variable
# name) — the trailing identifier keeps `#include <WebServer.h>` from matching.
# `.begin()` is too generic (Serial/Wire/SPIFFS all use it) to key on.
INO_ROUTE_RE='\.on\(["'\'']/'
INO_LISTEN_RE='\b(WiFiServer|EthernetServer|WebServer|AsyncWebServer|ESP8266WebServer|WiFiEspServer)[[:space:]]+[A-Za-z_]'

# Collapse indentation + internal whitespace runs, strip a trailing CR (CRLF
# files would otherwise leave \r embedded before the ` | exposure` column).
trim() { sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]\{2,\}/ /g' -e 's/\r$//'; }

# emit_kind FILE KIND REGEX EXPOSURE [grep-flags]
emit_kind() {
  local file=$1 kind=$2 re=$3 exposure=$4 flags=${5:-}
  # grep -n → LINE:content ; guard the no-match exit-1 under pipefail.
  # shellcheck disable=SC2086  # $flags is an optional grep flag, must word-split
  grep -n $flags -E "$re" "$file" 2>/dev/null | while IFS= read -r hit; do
    local lineno detail
    lineno=${hit%%:*}
    detail=$(printf '%s' "${hit#*:}" | trim)
    printf '%s:%s | %s | %s | %s\n' "$file" "$lineno" "$kind" "$detail" "$exposure"
  done
}

# --- main --------------------------------------------------------------------
found=0
while IFS= read -r file; do
  [ -n "$file" ] || continue
  exposure=$(detect_exposure "$file")
  out=$(
    emit_kind "$file" http-route "$HTTP_RE" "$exposure"
    emit_kind "$file" http-route "$HTTP_VERB_RE" "$exposure" -i
    emit_kind "$file" ws-handler "$WS_RE" "$exposure"
    emit_kind "$file" listener "$LISTEN_RE" "$exposure"
    case $file in *.sol) emit_kind "$file" contract-fn "$SOL_RE" "$exposure" ;; esac
    case $file in
      *.ino|*.cpp|*.cc|*.cxx|*.c|*.h|*.hpp|*.hh)
        emit_kind "$file" http-route "$INO_ROUTE_RE" "$exposure"
        emit_kind "$file" listener  "$INO_LISTEN_RE" "$exposure" ;;
    esac
  )
  if [ -n "$out" ]; then
    # A line can match >1 pattern (e.g. a route that is also a bind); collapse
    # exact-duplicate rows so each source line reports once per kind.
    printf '%s\n' "$out" | sort -u
    found=1
  fi
done < <(find_sources "$@" | sort)

# Exit 0 when entry points were found, 1 when none — lets callers branch on
# "has attack surface?" the way grep does, without treating empty as an error.
[ "$found" -eq 1 ]
