# C Review Checklist

## Correctness

- Verify function return values for all paths.
- Verify boundary handling (`n=0`, one-element arrays, not-found cases).
- Verify algorithm preconditions (for example binary search requires sorted input).
- Verify index base consistency (0-based vs 1-based outputs).

## Safety

- Verify allocated memory is freed.
- Verify pointer usage avoids out-of-bounds access.
- Verify string operations include required headers and bounded input where needed.

## Build

- Compile with strict flags: `-Wall -Wextra -Werror`.
- Ensure no implicit declarations or unused-variable warnings remain.
- A clean strict build does not rule out undefined behavior. Also build with `-fsanitize=address,undefined -fno-sanitize-recover=all` (`scripts/c_build_sanitize.sh`) and at `-O2`.

## Testing

- Run at least one found-case and one not-found-case for search tasks.
- Re-run the same sample I/O on the sanitizer build (`<name>.san`) and the `-O2` build. A result that differs between `-O0` and `-O2` points to undefined behavior first.
- Run judge script (`check.sh`) when available.
- Keep test execution reproducible and command-based.

## Reporting

- List findings by severity.
- Attach file references with line numbers.
- Explicitly state what was executed (compile/test commands).
- If the sanitizer or `-O2` runs were skipped, say so.
