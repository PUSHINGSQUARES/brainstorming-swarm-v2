# Public Surface Scrub Summary

## Scope

This repository begins with a fresh public root commit. Its Git history does not include the private development candidate. Test session IDs are deliberately fabricated UUIDs.

The release gate covers every tracked file, ordinary untracked files, ignored environment and key candidates, commit metadata, and every local Git object. It combines literal checks with independent reviews by people who know the private source context. A token scan alone cannot detect a recognizable example or an opaque identifier copied from a real session.

## Deterministic Checks

Run `python3 tests/check_public_tokens.py --patterns <private-pattern-file>` with the pattern file kept outside this repository. Run `python3 tests/check_public_surface.py paths` and `python3 tests/check_public_surface.py credentials --history` from the repository root. Run the full test suite and the host guide and support-matrix checks too.

The negative tests use invented values in disposable Git repositories. They cover tracked and untracked text, ignored environment and key files, JavaScript, filenames, Unix and Windows operator paths, current and historical credentials, UTF-16 history, and commit messages. Binary or undecodable candidates require review. Diagnostics identify a file and line or a Git object and line without echoing sensitive values.

## Independent Semantic Review

Two independent reviewers inspect the final public tree and local Git history with private context. One checks infrastructure, dispatch, and codename fingerprints. The other checks identity, brand voice, and recognizable examples. The reports remain outside this repository. Publication waits for both verdicts to pass on the final candidate.

Native host receipts and the final public publication decision are separate release gates.
