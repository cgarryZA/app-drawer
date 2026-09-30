#!/usr/bin/env bash
# Publish an APK to the app drawer. One fixed release tag per app; the asset is
# replaced in place, so the download URL never changes.
#
#   scripts/publish.sh bin-beacon path/to/app-release.apk [version]
#
# Needs a token with contents:write on cgarryZA/app-drawer. Locally `gh auth
# login` is enough. From another repository's CI, set GH_TOKEN to a
# fine-grained PAT scoped to this repo only.
#
# Deliberately NOT a version number in the tag - the whole point is a stable
# URL an invite link can hard-code. The version goes in the release body.

set -euo pipefail

REPO="cgarryZA/app-drawer"

APP="${1:-}"
APK="${2:-}"
VERSION="${3:-}"

if [ -z "$APP" ] || [ -z "$APK" ]; then
  echo "usage: $0 <app-slug> <path-to-apk> [version]" >&2
  echo "  e.g. $0 bin-beacon build/app/outputs/flutter-apk/app-release.apk 0.1.2" >&2
  exit 2
fi

case "$APP" in
  *[!a-z0-9-]*) echo "app slug must be lower-case letters, digits and dashes: $APP" >&2; exit 2 ;;
esac

if [ ! -f "$APK" ]; then
  echo "no such file: $APK" >&2
  exit 1
fi

# An APK that is not an APK is the failure worth catching here: a zero-byte
# build output, or a path that resolved to the wrong thing, would otherwise be
# published under a URL people already have.
if ! head -c 2 "$APK" | grep -q "PK"; then
  echo "$APK does not look like an APK (no PK zip header)" >&2
  exit 1
fi

SIZE_MB=$(( $(wc -c < "$APK") / 1024 / 1024 ))
echo "publishing $APP  ${SIZE_MB} MB  from $APK"

NOTES="Rolling release - the asset is replaced in place, so the download URL is stable."
if [ -n "$VERSION" ]; then
  NOTES="Version ${VERSION}, built $(date -u +%Y-%m-%d). ${NOTES}"
fi
if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
  NOTES="${NOTES}"$'\n\n'"Source commit: $(git rev-parse --short HEAD) (private repository)."
fi

if ! gh release view "$APP" --repo "$REPO" >/dev/null 2>&1; then
  gh release create "$APP" --repo "$REPO" --title "$APP" --notes "$NOTES"
  echo "created release $APP"
else
  gh release edit "$APP" --repo "$REPO" --notes "$NOTES" >/dev/null
fi

# Upload under the app's own name, not the build system's `app-release.apk` -
# the filename is what the person downloading sees and taps.
TMP="$(mktemp -d)"
cp "$APK" "$TMP/${APP}.apk"
gh release upload "$APP" "$TMP/${APP}.apk" --repo "$REPO" --clobber
rm -rf "$TMP"

echo
echo "download URL (stable):"
echo "  https://github.com/${REPO}/releases/download/${APP}/${APP}.apk"
echo
echo "The download page rebuilds itself from the releases within a minute."
