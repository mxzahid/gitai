"""Tests for diff collection and chunking."""

from gitai.diff import DiffChunk, StagedDiff


class TestStagedDiff:
    """Test StagedDiff functionality."""

    def test_empty_diff(self):
        """Test handling of empty diff."""
        diff = StagedDiff("")
        assert diff.is_empty()
        assert diff.files == []
        assert diff.stats["files_changed"] == 0

    def test_single_file_diff(self):
        """Test parsing single file diff."""
        diff_content = """diff --git a/README.md b/README.md
index 1234567..abcdef0 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 Hello World
+New line added
"""
        diff = StagedDiff(diff_content)
        assert not diff.is_empty()
        assert diff.files == ["README.md"]
        assert diff.stats["files_changed"] == 1
        assert diff.stats["additions"] == 1
        assert diff.stats["deletions"] == 0

    def test_multiple_files_diff(self):
        """Test parsing multiple files diff."""
        diff_content = """diff --git a/file1.py b/file1.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/file1.py (new file)
@@ -0,0 +1,10 @@
+def hello():
+    print("hello")

diff --git a/file2.py b/file2.py
index abcdef0..1234567 100644
--- a/file2.py
+++ b/file2.py
@@ -1,5 +1,3 @@
 def hello():
-    print("hello")
-    print("world")
+    print("hello world")
"""
        diff = StagedDiff(diff_content)
        assert not diff.is_empty()
        assert set(diff.files) == {"file1.py", "file2.py"}
        assert diff.stats["files_changed"] == 2
        assert diff.stats["new_files"] == 1
        assert diff.stats["additions"] == 3
        assert diff.stats["deletions"] == 2

    def test_chunk_by_files_small_diff(self):
        """Test chunking with small diff."""
        diff_content = """diff --git a/small.py b/small.py
index 1234567..abcdef0 100644
--- a/small.py
+++ b/small.py
@@ -1 +1,2 @@
 Hello
+World
"""
        diff = StagedDiff(diff_content)
        chunks = diff.chunk_by_files(max_size=1000)

        assert len(chunks) == 1
        assert chunks[0].files == ["small.py"]
        assert "Hello" in chunks[0].content
        assert "World" in chunks[0].content

    def test_chunk_by_files_large_diff(self):
        """Test chunking with large diff that exceeds size limit."""
        # Create a large diff content
        large_content = "diff --git a/large.py b/large.py\n"
        large_content += "index 1234567..abcdef0 100644\n"
        large_content += "--- a/large.py\n+++ b/large.py\n"
        large_content += "@@ -1 +1 @@\n"
        large_content += "-old content\n"
        large_content += "+" + "x" * 1000 + "\n"  # Large content

        diff = StagedDiff(large_content)
        chunks = diff.chunk_by_files(max_size=500)  # Small limit to force chunking

        assert len(chunks) == 1  # Should still be 1 chunk since it's one file
        assert chunks[0].files == ["large.py"]


class TestDiffChunk:
    """Test DiffChunk functionality."""

    def test_chunk_creation(self):
        """Test creating a diff chunk."""
        content = "diff content here"
        files = ["file1.py", "file2.py"]

        chunk = DiffChunk(content, files)

        assert chunk.content == content
        assert chunk.files == files
        assert chunk.size == len(content)

    def test_chunk_string_representation(self):
        """Test string representation of chunk."""
        content = "diff content"
        files = ["file1.py"]

        chunk = DiffChunk(content, files)

        assert str(chunk) == "DiffChunk(1 files, 12 chars)"
