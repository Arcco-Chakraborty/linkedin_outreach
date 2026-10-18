# Handoff

## Status snapshot
- Privacy cleanup is prepared locally. All reachable source history was sanitized;
  real environment files, browser sessions, lead exports, logs and bytecode were
  removed. Contact examples now use reserved example domains.
- Application authentication and Apollo lookup behavior are unchanged.
- Empty configuration/cookie references and invented CSV examples are provided.

## In progress
- Local verification completed; independent review and repository migration remain.
- Offline applicable suite: 66 passed, including 3 new safe-example/ignore checks.
- Full offline suite: 66 passed, the same 9 pre-existing pipeline failures.
- Original-history privacy check fails; sanitized history passes. No production
  Python source changed apart from checkout line endings.

## Next steps (ordered)
1. Re-run the public history checker on the final committed head.
2. Have the coordinating maintainer independently review the sanitized history.
3. Publish only the clean history through the maintainer's approved repository
   migration procedure. Rewriting local Git does not clear hosted cached objects.

## Decisions (append-only)
- Preserve code history and application interfaces; remove private runtime data
  throughout every reachable revision and keep it ignored going forward.
- Author contact metadata uses the repository owner's GitHub noreply address.
- Keep the obsolete pipeline tests unchanged during privacy cleanup. Original
  offline baseline: 63 passed, 9 failed, all in tests/test_pipeline.py. Those tests
  still target removed SMTP pipeline functions; current pipeline uses Apollo.
- No browser login, provider API call or SMTP delivery is part of verification.

## Key facts & pointers
- README.md documents setup, optional Apollo keys and first-run browser login.
- src/session.py: an absent cookie file starts login; an existing empty file does
  not. The empty cookie example is for reference, not a runtime file to copy.
- tools/check_public_history.py checks every reachable ref for private runtime
  paths and contact examples. Exact original-private-value checks live outside
  this public source tree with the coordinating maintainer's audit evidence.

## How to resume from cold
Read this file, run the public history checker and offline tests, then inspect the
coordinating maintainer's separate migration/audit evidence before any publication.
