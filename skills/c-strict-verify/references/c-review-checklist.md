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

## Testing

- Run at least one found-case and one not-found-case for search tasks.
- Run judge script (`check.sh`) when available.
- Keep test execution reproducible and command-based.

## Reporting

- List findings by severity.
- Attach file references with line numbers.
- Explicitly state what was executed (compile/test commands).
