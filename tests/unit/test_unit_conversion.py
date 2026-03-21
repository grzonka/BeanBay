"""Tests for pint-based unit conversion utilities."""

import pytest

from beanbay.utils.units import (
    apply_unit_conversion,
    convert_flow_rate,
    convert_pressure,
    convert_temperature,
    convert_weight,
)


class TestConvertWeight:
    def test_grams_to_ounces(self):
        result = convert_weight(100, True)
        assert result == pytest.approx(3.527, abs=0.001)

    def test_no_conversion(self):
        result = convert_weight(100, False)
        assert result == 100


class TestConvertTemperature:
    def test_celsius_to_fahrenheit(self):
        result = convert_temperature(93, True)
        assert result == pytest.approx(199.4, abs=0.1)

    def test_freezing_point(self):
        result = convert_temperature(0, True)
        assert result == pytest.approx(32.0, abs=0.01)


class TestConvertPressure:
    def test_bar_to_psi(self):
        result = convert_pressure(9, True)
        assert result == pytest.approx(130.5, abs=0.5)


class TestConvertFlowRate:
    def test_ml_per_s_to_floz_per_s(self):
        result = convert_flow_rate(1.5, True)
        # 1 ml ≈ 0.033814 fl oz, so 1.5 ml/s ≈ 0.0507 fl oz/s
        assert result == pytest.approx(0.0507, abs=0.002)


class TestRoundTrip:
    def test_weight_round_trip(self):
        original = 18.5
        imperial = convert_weight(original, True)
        # Convert back: ounces to grams
        from beanbay.utils.units import Q_

        back = Q_(imperial, "ounce").to("gram").magnitude
        assert back == pytest.approx(original, abs=0.01)

    def test_temperature_round_trip(self):
        original = 93.0
        imperial = convert_temperature(original, True)
        from beanbay.utils.units import Q_

        back = Q_(imperial, "degF").to("degC").magnitude
        assert back == pytest.approx(original, abs=0.01)

    def test_pressure_round_trip(self):
        original = 9.0
        imperial = convert_pressure(original, True)
        from beanbay.utils.units import Q_

        back = Q_(imperial, "psi").to("bar").magnitude
        assert back == pytest.approx(original, abs=0.01)


class TestApplyUnitConversion:
    def test_imperial_false_returns_unchanged(self):
        data = {"dose": 18.0, "temperature": 93.0, "name": "espresso"}
        result = apply_unit_conversion(data, imperial=False)
        assert result is data  # same object, not even copied

    def test_imperial_true_converts_known_fields(self):
        data = {
            "dose": 18.0,
            "yield_amount": 36.0,
            "weight": 250.0,
            "temperature": 93.0,
            "temp_min": 85.0,
            "temp_max": 96.0,
            "temp_step": 1.0,
            "pressure": 9.0,
            "pressure_min": 6.0,
            "pressure_max": 12.0,
            "flow_rate": 1.5,
            "saturation_flow_rate": 2.0,
            "name": "espresso",
            "grind_setting": 15,
        }
        result = apply_unit_conversion(data, imperial=True)

        # Weight fields converted
        assert result["dose"] == pytest.approx(0.635, abs=0.001)
        assert result["yield_amount"] == pytest.approx(1.270, abs=0.001)
        assert result["weight"] == pytest.approx(8.818, abs=0.001)

        # Temperature fields converted
        assert result["temperature"] == pytest.approx(199.4, abs=0.1)
        assert result["temp_min"] == pytest.approx(185.0, abs=0.1)
        assert result["temp_max"] == pytest.approx(204.8, abs=0.1)
        assert result["temp_step"] == pytest.approx(33.8, abs=0.1)

        # Pressure fields converted
        assert result["pressure"] == pytest.approx(130.5, abs=0.5)
        assert result["pressure_min"] == pytest.approx(87.0, abs=0.5)
        assert result["pressure_max"] == pytest.approx(174.0, abs=0.5)

        # Flow rate fields converted
        assert result["flow_rate"] == pytest.approx(0.0507, abs=0.002)
        assert result["saturation_flow_rate"] == pytest.approx(0.0676, abs=0.002)

        # Non-converted fields untouched
        assert result["name"] == "espresso"
        assert result["grind_setting"] == 15

    def test_handles_none_values(self):
        data = {
            "dose": 18.0,
            "yield_amount": None,
            "temperature": None,
            "pressure": None,
            "flow_rate": None,
            "name": "test",
        }
        result = apply_unit_conversion(data, imperial=True)
        assert result["dose"] == pytest.approx(0.635, abs=0.001)
        assert result["yield_amount"] is None
        assert result["temperature"] is None
        assert result["pressure"] is None
        assert result["flow_rate"] is None
        assert result["name"] == "test"
