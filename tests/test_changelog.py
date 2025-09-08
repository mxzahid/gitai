"""Tests for changelog generation."""

from unittest.mock import Mock, patch

import pytest

from gitai.changelog import ChangelogGenerator


class TestChangelogGenerator:
    """Test ChangelogGenerator functionality."""

    @pytest.fixture
    def config(self, tmp_path):
        """Create a test config."""
        config = Mock()
        config.llm = Mock()
        config.llm.provider = "openai"
        config.llm.api_key = "test-key"
        config.llm.model = "gpt-4o-mini"
        config.llm.max_tokens = 300
        config.llm.temperature = 0.0
        config.llm.timeout_seconds = 45
        config.git_root = tmp_path
        config.is_llm_available.return_value = True
        return config

    @pytest.fixture
    def sample_commits(self):
        """Sample commit data for testing."""
        return [
            {
                "hash": "abc123",
                "subject": "feat: add user authentication",
                "body": "Implements user login and registration\n\nFixes #123",
            },
            {
                "hash": "def456",
                "subject": "fix(api): handle null pointer exception",
                "body": "Fix crash when user data is null\n\nCloses #456",
            },
            {
                "hash": "ghi789",
                "subject": "docs: update README with installation instructions",
                "body": "",
            },
            {
                "hash": "jkl012",
                "subject": "chore: update dependencies",
                "body": "Bump version of requests library",
            },
            {
                "hash": "mno345",
                "subject": "refactor(core): simplify user validation logic",
                "body": "",
            },
        ]

    @patch("gitai.changelog.get_commit_history")
    def test_group_commits_by_type(self, mock_get_history, config, sample_commits):
        """Test grouping commits by conventional commit types."""
        mock_get_history.return_value = sample_commits

        generator = ChangelogGenerator(config)
        grouped = generator._group_commits(sample_commits)

        assert "Features" in grouped
        assert "Fixes" in grouped
        assert "Documentation" in grouped
        assert "Chore" in grouped
        assert "Refactoring" in grouped

        assert "add user authentication (#123)" in grouped["Features"]
        assert "**api:** handle null pointer exception (#456)" in grouped["Fixes"]
        assert (
            "update README with installation instructions" in grouped["Documentation"]
        )

    @patch("gitai.changelog.get_commit_history")
    def test_generate_raw_changelog(self, mock_get_history, config, sample_commits):
        """Test generating raw changelog without LLM."""
        mock_get_history.return_value = sample_commits

        generator = ChangelogGenerator(config)
        grouped = generator._group_commits(sample_commits)
        changelog = generator._generate_raw_changelog(grouped, "1.0.0")

        assert "## [1.0.0]" in changelog
        assert "### Features" in changelog
        assert "### Fixes" in changelog
        assert "- add user authentication (#123)" in changelog
        assert "- **api:** handle null pointer exception (#456)" in changelog

    @patch("gitai.changelog.get_commit_history")
    def test_generate_raw_changelog_no_version(
        self, mock_get_history, config, sample_commits
    ):
        """Test generating raw changelog without version (uses date)."""
        mock_get_history.return_value = sample_commits

        generator = ChangelogGenerator(config)
        grouped = generator._group_commits(sample_commits)
        changelog = generator._generate_raw_changelog(grouped, None)

        assert "## 20" in changelog  # Should contain year

    @patch("gitai.changelog.get_commit_history")
    def test_extract_pr_references(self, mock_get_history, config):
        """Test extracting PR/issue references from commit bodies."""
        commits_with_refs = [
            {
                "hash": "abc123",
                "subject": "feat: add feature",
                "body": "Fixes #123 and closes #456\nAlso addresses GH-789",
            },
            {
                "hash": "def456",
                "subject": "fix: bug fix",
                "body": "PR #999\nPull Request #888",
            },
        ]
        mock_get_history.return_value = commits_with_refs

        generator = ChangelogGenerator(config)
        grouped = generator._group_commits(commits_with_refs)

        # Check that PR references are included
        feature_item = grouped["Features"][0]
        assert "#123" in feature_item
        assert "#456" in feature_item
        assert "#789" in feature_item

    @patch("gitai.changelog.get_commit_history")
    def test_polish_with_llm(self, mock_get_history, config, sample_commits):
        """Test polishing changelog with LLM."""
        mock_get_history.return_value = sample_commits

        with patch("gitai.changelog.create_provider") as mock_create_provider:
            mock_provider = Mock()
            mock_provider.generate.return_value = """- Add user authentication system
- Fix null pointer exception in API
- Update README documentation
- Update project dependencies
- Simplify user validation logic"""
            mock_create_provider.return_value = mock_provider

            generator = ChangelogGenerator(config)
            grouped = generator._group_commits(sample_commits)

            raw_content = generator._generate_raw_changelog(grouped, "1.0.0")
            polished = generator._polish_with_llm(raw_content)

            assert "Add user authentication system" in polished
            mock_provider.generate.assert_called_once()

    @patch("gitai.changelog.get_commit_history")
    def test_insert_into_new_changelog(
        self, mock_get_history, config, sample_commits, tmp_path
    ):
        """Test inserting changelog into new file."""
        mock_get_history.return_value = sample_commits

        changelog_path = tmp_path / "CHANGELOG.md"
        generator = ChangelogGenerator(config)

        result = generator._insert_into_changelog(
            "## [1.0.0] - 2024-01-01\n\n### Features\n- New feature", changelog_path
        )

        assert "Created new changelog" in result
        assert changelog_path.exists()

        content = changelog_path.read_text()
        assert "## [1.0.0] - 2024-01-01" in content

    @patch("gitai.changelog.get_commit_history")
    def test_insert_into_existing_changelog(
        self, mock_get_history, config, sample_commits, tmp_path
    ):
        """Test inserting changelog into existing file."""
        mock_get_history.return_value = sample_commits

        changelog_path = tmp_path / "CHANGELOG.md"
        existing_content = (
            "# Changelog\n\n## [0.9.0] - 2023-12-01\n\n### Features\n- Old feature\n"
        )
        changelog_path.write_text(existing_content)

        generator = ChangelogGenerator(config)

        result = generator._insert_into_changelog(
            "## [1.0.0] - 2024-01-01\n\n### Features\n- New feature", changelog_path
        )

        assert "Updated changelog" in result

        content = changelog_path.read_text()
        # New content should be inserted at the top
        lines = content.split("\n")
        assert lines[0] == "## [1.0.0] - 2024-01-01"
        assert "## [0.9.0] - 2023-12-01" in lines
        assert "# Changelog" in lines

    @patch("gitai.changelog.get_commit_history")
    def test_no_commits_found(self, mock_get_history, config):
        """Test handling when no commits are found."""
        mock_get_history.return_value = []

        generator = ChangelogGenerator(config)
        result = generator.generate_changelog("v1.0.0", "HEAD")

        assert "No commits found" in result

    def test_non_conventional_commits(self, config):
        """Test handling non-conventional commit messages."""
        non_conventional_commits = [
            {
                "hash": "abc123",
                "subject": "Add new feature without conventional format",
                "body": "",
            },
            {
                "hash": "def456",
                "subject": "fix: proper conventional commit",
                "body": "",
            },
        ]

        generator = ChangelogGenerator(config)
        grouped = generator._group_commits(non_conventional_commits)

        assert "Other" in grouped
        assert "Fixes" in grouped
        assert "Add new feature without conventional format" in grouped["Other"]
        assert "proper conventional commit" in grouped["Fixes"]
