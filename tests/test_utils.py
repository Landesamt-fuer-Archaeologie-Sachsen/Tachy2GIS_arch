import pytest

from Tachy2GIS_arch.common.utils import any2bool, isNumber, natural_sort_key, FileFunctions


# ---------------------------------------------------------------------------
# natural_sort_key()
# ---------------------------------------------------------------------------


class TestNaturalSortKey:
    def test_numeric_parts_sort_by_value(self):
        names = ["file10", "file2", "file1", "file20"]
        sorted_names = sorted(names, key=natural_sort_key)
        assert sorted_names == ["file1", "file2", "file10", "file20"]

    def test_plain_strings_sort_lexicographically(self):
        names = ["beta", "alpha", "gamma"]
        assert sorted(names, key=natural_sort_key) == ["alpha", "beta", "gamma"]

    def test_mixed_prefix_and_number(self):
        names = ["img_9", "img_10", "img_100", "img_2"]
        assert sorted(names, key=natural_sort_key) == ["img_2", "img_9", "img_10", "img_100"]

    def test_case_insensitive(self):
        names = ["B_1", "a_2", "c_3"]
        assert sorted(names, key=natural_sort_key) == ["a_2", "B_1", "c_3"]


# ---------------------------------------------------------------------------
# isNumber()
# ---------------------------------------------------------------------------


class TestIsNumber:
    def test_integer_string_is_number(self):
        assert isNumber("42") is True

    def test_float_string_is_number(self):
        assert isNumber("3.14") is True

    def test_negative_number_is_number(self):
        assert isNumber("-7") is True

    def test_zero_is_number(self):
        assert isNumber("0") is True

    def test_empty_string_is_not_number(self):
        assert isNumber("") is False

    def test_alpha_string_is_not_number(self):
        assert isNumber("abc") is False

    def test_none_is_not_number(self):
        assert isNumber(None) is False


# ---------------------------------------------------------------------------
# any2bool()
# ---------------------------------------------------------------------------


class TestAny2Bool:
    @pytest.mark.parametrize("value", ["on", "an", "ja", "j", "yes", "y", "true", "t", "wahr", "1", "2", "True", True])
    def test_truthy_values(self, value):
        assert any2bool(value) is True

    @pytest.mark.parametrize("value", ["off", "aus", "nein", "n", "no", "false", "f", "falsch", "False", False])
    def test_falsy_values(self, value):
        assert any2bool(value) is False

    def test_none_raises_value_error(self):
        # any2bool(None) falls through the None-guard and reaches the raise.
        # This is a known edge case in the current implementation.
        with pytest.raises(ValueError):
            any2bool(None)

    def test_invalid_string_raises_value_error(self):
        with pytest.raises(ValueError):
            any2bool("vielleicht")

    def test_bool_true_passthrough(self):
        assert any2bool(True) is True

    def test_bool_false_passthrough(self):
        assert any2bool(False) is False

    def test_numeric_zero_string_resolves_via_isnumber(self):
        # "0" passes isNumber(), so any2bool returns bool("0") which is True
        # (non-empty string). Use the integer 0 or False for falsy numeric input.
        assert any2bool("0") is True

    def test_numeric_nonzero_is_true(self):
        assert any2bool("1") is True


# ---------------------------------------------------------------------------
# FileFunctions
# ---------------------------------------------------------------------------


class TestFileFunctions:
    def test_file_copy_creates_target(self, tmp_path):
        src = tmp_path / "source.txt"
        src.write_text("Tachy2GIS")
        dst = tmp_path / "dest.txt"
        FileFunctions.file_copy(str(src), str(dst))
        assert dst.exists()
        assert dst.read_text() == "Tachy2GIS"

    def test_file_copy_skips_when_source_missing(self, tmp_path):
        dst = tmp_path / "dest.txt"
        FileFunctions.file_copy(str(tmp_path / "nonexistent.txt"), str(dst))
        assert not dst.exists()

    def test_file_del_removes_file(self, tmp_path):
        f = tmp_path / "to_delete.txt"
        f.write_text("delete me")
        FileFunctions.file_del(str(f))
        assert not f.exists()

    def test_file_del_does_not_raise_when_missing(self, tmp_path):
        FileFunctions.file_del(str(tmp_path / "nonexistent.txt"))

    def test_directory_copy_copies_contents(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.txt").write_text("alpha")
        (src / "b.txt").write_text("beta")
        dst = tmp_path / "dst"
        result = FileFunctions.directory_copy(str(src), str(dst))
        assert result is True
        assert (dst / "a.txt").read_text() == "alpha"
        assert (dst / "b.txt").read_text() == "beta"

    def test_directory_copy_returns_false_when_destination_exists(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        dst = tmp_path / "dst"
        dst.mkdir()
        result = FileFunctions.directory_copy(str(src), str(dst))
        assert result is False

    def test_directory_copy_excludes_top_level_dirs(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "keep.txt").write_text("keep")
        excluded = src / "skip_me"
        excluded.mkdir()
        (excluded / "secret.txt").write_text("secret")
        dst = tmp_path / "dst"
        FileFunctions.directory_copy(str(src), str(dst), exclude_dirs_on_top_level=["skip_me"])
        assert (dst / "keep.txt").exists()
        assert not (dst / "skip_me").exists()
