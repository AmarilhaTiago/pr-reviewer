# php-loose-comparison

`strpos(...) == false` is true when the match is at position 0.

Expected: `app/Support/PathGuard.php:14` (bug).
