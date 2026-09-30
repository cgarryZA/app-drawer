# app-drawer

Public download page for the small Android apps I build. The source for most of
them is private; this repo holds only the signed APKs and the page that links
to them.

**Download page: https://cgarryza.github.io/app-drawer/**

## Why this exists

An install link has to be reachable by someone who is not me - a housemate
joining a Bin Beacon household, say. That rules out the private source repo
(its release assets need authentication) and the app drawer on the Pi (behind
Cloudflare Access). Putting a 20 MB APK inside a Cloudflare Worker's asset
bundle also does not work: the per-asset cap is 25 MiB, and sizing an app to
fit its hosting is the wrong way round.

A public GitHub release is free, CDN-backed, allows 2 GB per file, and costs
no new infrastructure.

## The URL convention

One **fixed release tag per app**, never a version number, with the APK
attached under a stable filename. Uploads use `--clobber`, so the tag is
updated in place and the download URL never changes:

```
https://github.com/cgarryZA/app-drawer/releases/download/<app>/<app>.apk
```

For example `.../releases/download/bin-beacon/bin-beacon.apk`.

Do **not** use `/releases/latest/download/...` here. "Latest" is per-repo, not
per-app, so with several apps in one repo it resolves to whichever app was
published most recently.

Each release body carries the version, the build date and the source commit,
so a downloaded APK can be traced back even though the source is private.

## Publishing a build

From CI in the app's own repository, once the signed APK exists:

```bash
gh release view "$APP" --repo cgarryZA/app-drawer >/dev/null 2>&1 \
  || gh release create "$APP" --repo cgarryZA/app-drawer \
       --title "$APP" --notes "Rolling release. The asset is replaced in place."
gh release upload "$APP" "dist/$APP.apk" --repo cgarryZA/app-drawer --clobber
```

This needs a token with `contents: write` on **this** repo. The automatic
`GITHUB_TOKEN` is scoped to the repository the workflow runs in, so a
cross-repository upload needs a fine-grained personal access token, stored as
a secret in the source repo (`APP_DRAWER_TOKEN`) and passed as `GH_TOKEN`.

Scope it to this repository only, with `Contents: Read and write`. Nothing
here is sensitive, so a leak of that token costs an unwanted APK upload to a
public repo and nothing else - which is the point of scoping it narrowly
rather than reusing a broad token.

## Installing on Android

These are not on Google Play, so Android asks for permission the first time:

1. Open the download link in a browser and let the `.apk` download.
2. Tap it. Android will offer to allow installs from that browser - accept,
   then come back and tap the file again.
3. Play Protect may warn that the app is unrecognised. "Install anyway".

An app installs over its previous version and keeps its data, as long as the
signing key has not changed.

## What is safe to put here

Anything here is public and permanently downloadable by anyone who guesses or
is given the URL. That is fine for these apps, whose security does not rest on
the binary being secret - a Bin Beacon household is protected by its invite
code and member keys, not by nobody having the app.

It is **not** fine for an APK carrying a baked-in API key, token or password.
Check before publishing a new app here.

## The page

`docs/index.html` is generated from this repo's releases by
`.github/workflows/index.yml`, which runs whenever a release is published or
edited, and can be run by hand from the Actions tab. Do not edit the HTML
directly - the next release will overwrite it. GitHub Actions is free on
public repositories, so this costs nothing.
