import pytest

from Tachy2GIS_arch.tachyconnect_t2g.GSI_Parser import parse, make_vertex


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GSI16_FULL_LINE = (
    "*11....+0000000000000473 "
    "21.022+0000000039809400 "
    "22.022+0000000010859950 "
    "31..00+0000000000000609 "
    "81..00+0000000565385748 "
    "82..00+0000005924615105 "
    "83..00+0000000000005224 "
    "87..10+0000000000000000 \r\n"
)

GSI8_FULL_LINE = "11....+00000473 " "81..00+65385748 " "82..00+24615105 " "83..00+00005224\r\n"


# ---------------------------------------------------------------------------
# parse() – format detection
# ---------------------------------------------------------------------------


class TestParseFormatDetection:
    def test_gsi16_sets_precision_16(self):
        result, _ = parse(GSI16_FULL_LINE)
        assert result["precision"] == 16

    def test_gsi8_sets_precision_8(self):
        result, _ = parse(GSI8_FULL_LINE)
        assert result["precision"] == 8

    def test_empty_line_returns_empty_dict(self):
        result, units = parse("")
        assert result == {}
        assert units == {}

    def test_short_line_returns_empty_dict(self):
        result, units = parse("***")
        assert result == {}
        assert units == {}


# ---------------------------------------------------------------------------
# parse() – coordinate extraction and decimal-point correction
# ---------------------------------------------------------------------------


class TestParseCoordinates:
    def test_target_coordinates_are_present(self):
        result, _ = parse(GSI16_FULL_LINE)
        assert "targetX" in result
        assert "targetY" in result
        assert "targetZ" in result

    def test_target_x_decimal_correction(self):
        # unit "0" = meter_1mm  ->  divider 1000
        # raw value 0000000565385748  ->  565385.748
        result, _ = parse(GSI16_FULL_LINE)
        assert result["targetX"] == pytest.approx(565385.748)

    def test_target_y_decimal_correction(self):
        # raw value 0000005924615105  ->  5924615.105
        result, _ = parse(GSI16_FULL_LINE)
        assert result["targetY"] == pytest.approx(5924615.105)

    def test_target_z_decimal_correction(self):
        # raw value 0000000000005224  ->  5.224
        result, _ = parse(GSI16_FULL_LINE)
        assert result["targetZ"] == pytest.approx(5.224)

    def test_point_id_is_parsed_as_text(self):
        result, _ = parse(GSI16_FULL_LINE)
        assert result["pointId"] == "0000000000000473"

    def test_units_dict_populated(self):
        _, units = parse(GSI16_FULL_LINE)
        assert units.get("targetX") == "meter_1mm"
        assert units.get("targetY") == "meter_1mm"
        assert units.get("targetZ") == "meter_1mm"


# ---------------------------------------------------------------------------
# parse() – sign handling
# ---------------------------------------------------------------------------


class TestParseSign:
    def test_negative_value_inverted(self):
        # Replace sign byte '+' with '-' for targetX word.
        # Word structure: "81..00+0000000565385748"
        #                            ^ position 6 is sign
        negative_line = GSI16_FULL_LINE.replace("81..00+0000000565385748", "81..00-0000000565385748")
        result, _ = parse(negative_line)
        assert result["targetX"] == pytest.approx(-565385.748)

    def test_positive_sign_unchanged(self):
        result, _ = parse(GSI16_FULL_LINE)
        assert result["targetX"] > 0


class TestParseRobustness:
    def test_real_world_line_produces_valid_vertex(self):
        # Regression line that caused errors in an older parser version.
        line = (
            "*110009+0000000000000031 "
            "21.324+0000000011604363 "
            "22.324+0000000011608245 "
            "31..06+0000000000033649 "
            "51....+000000000008+034 "
            "87..16+0000000000000000 "
            "81..06+0000000000046612 "
            "82..06-0000000000022604 "
            "83..06+0000000000000000"
        )
        x, y, z = make_vertex(line)
        assert x == pytest.approx(4.6612)
        assert y == pytest.approx(-2.2604)
        assert z == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# make_vertex()
# ---------------------------------------------------------------------------


class TestMakeVertex:
    def test_returns_xyz_tuple(self):
        x, y, z = make_vertex(GSI16_FULL_LINE)
        assert x == pytest.approx(565385.748)
        assert y == pytest.approx(5924615.105)
        assert z == pytest.approx(5.224)

    def test_raises_when_z_missing(self):
        # Build a line without the Z word (83..).
        no_z_line = "*11....+0000000000000473 " "81..00+0000000565385748 " "82..00+0000005924615105\r\n"
        with pytest.raises(ValueError, match="No z coordinate"):
            make_vertex(no_z_line)
