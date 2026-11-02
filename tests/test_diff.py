from reviewer.diff import parse_diff

TWO_FILES = """diff --git a/app/a.py b/app/a.py
index 111..222 100644
--- a/app/a.py
+++ b/app/a.py
@@ -1,3 +1,4 @@
 import os
+import sys
 x = 1
-y = 2
+y = 3
@@ -10,2 +11,3 @@ def f():
 a = 1
+b = 2
 c = 3
diff --git a/b.php b/b.php
index 333..444 100644
--- a/b.php
+++ b/b.php
@@ -5,1 +5,2 @@
 $a = 1;
+$b = 2;
"""


def test_two_files_with_hunks():  # AC1
    files = parse_diff(TWO_FILES)
    assert [f.path for f in files] == ["app/a.py", "b.php"]
    assert [len(f.hunks) for f in files] == [2, 1]
    assert files[0].status == "modified"
    assert files[0].hunks[0].new_start == 1
    assert files[0].hunks[1].new_start == 11


def test_added_line_numbers_in_new_file():  # AC2
    files = parse_diff(TWO_FILES)
    assert files[0].added_lines == {2: "import sys", 4: "y = 3", 12: "b = 2"}
    assert files[1].added_lines == {6: "$b = 2;"}


def test_removed_lines_have_no_number():  # AC2
    hunk = parse_diff(TWO_FILES)[0].hunks[0]
    removed = [line for line in hunk.lines if line.kind == "-"]
    assert [line.new_number for line in removed] == [None]


def test_new_file():  # AC3
    diff = """diff --git a/n.py b/n.py
new file mode 100644
index 000..111
--- /dev/null
+++ b/n.py
@@ -0,0 +1,2 @@
+a = 1
+b = 2
"""
    (f,) = parse_diff(diff)
    assert (f.path, f.status) == ("n.py", "added")
    assert f.added_lines == {1: "a = 1", 2: "b = 2"}


def test_deleted_file():  # AC3
    diff = """diff --git a/d.py b/d.py
deleted file mode 100644
index 111..000
--- a/d.py
+++ /dev/null
@@ -1,1 +0,0 @@
-a = 1
"""
    (f,) = parse_diff(diff)
    assert (f.path, f.status) == ("d.py", "deleted")
    assert f.added_lines == {}


def test_pure_rename_without_hunks():  # AC3
    diff = """diff --git a/old.py b/new.py
similarity index 100%
rename from old.py
rename to new.py
"""
    (f,) = parse_diff(diff)
    assert (f.path, f.old_path, f.status) == ("new.py", "old.py", "renamed")
    assert f.hunks == []


def test_binary_file():  # AC3
    diff = """diff --git a/i.png b/i.png
index 111..222 100644
Binary files a/i.png and b/i.png differ
"""
    (f,) = parse_diff(diff)
    assert f.is_binary and f.hunks == []


def test_no_newline_marker_ignored_and_empty_input():  # AC4
    diff = """diff --git a/a.txt b/a.txt
--- a/a.txt
+++ b/a.txt
@@ -1,1 +1,1 @@
-a
\ No newline at end of file
+b
\ No newline at end of file
"""
    (f,) = parse_diff(diff)
    assert f.added_lines == {1: "b"}
    assert parse_diff("") == []
