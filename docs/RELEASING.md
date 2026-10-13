# Private App release

Use the single `android-lite.yml` workflow on `recipe` in the private
`Celestials316/nodejs-mobile-app-lite` repository. Select `build` to
retain tested private artifacts or `build-and-release` to publish a tested
private prerelease in the same run. Optional `release_tag` selects an unused
`app-lite-v24.22.0-1[-suffix]` tag; empty uses this workflow's unique run ID.
`release_notes` appends optional English notes to the reviewed notes file.

Publication checks private repository visibility at preparation and upload,
validates the source checksum, and packages all three Android App ABIs.
Failed build or device gates prevent packaging and publication. Tags point
to verified complete-source snapshot commits with recipe/tree provenance.
Assets upload into a draft; the release becomes visible only after all files
are attached. No public repository or release is changed.

If publication is interrupted after tag creation, inspect the original run
and rerun its publish job; it checks the existing tag's tree and recipe commit
and only resumes a draft. Published releases are not overwritten. New build
runs must use new tags. Changing the source requires committing/regenerating
the matching recipe tree before dispatch.
