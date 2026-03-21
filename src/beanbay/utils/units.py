"""Pint-based unit conversion between metric and imperial systems.

TODO: Wire ``?units=metric|imperial`` query param into routers. The conversion
functions are ready but not yet integrated into endpoint serialization. See
spec section 3.9 for the field list and expected behavior.
"""

from pint import UnitRegistry

ureg = UnitRegistry(cache_folder=":auto:")
Q_ = ureg.Quantity  # type: ignore[type-arg]


def convert_weight(value: float, to_imperial: bool) -> float:
    """Convert weight between grams and ounces.

    Parameters
    ----------
    value : float
        Weight value in grams.
    to_imperial : bool
        If True, convert grams to ounces. If False, return unchanged.

    Returns
    -------
    float
        Weight in ounces (if converting) or original grams value.
    """
    if to_imperial:
        return Q_(value, "gram").to("ounce").magnitude
    return value


def convert_temperature(value: float, to_imperial: bool) -> float:
    """Convert temperature between celsius and fahrenheit.

    Parameters
    ----------
    value : float
        Temperature value in degrees Celsius.
    to_imperial : bool
        If True, convert Celsius to Fahrenheit. If False, return unchanged.

    Returns
    -------
    float
        Temperature in Fahrenheit (if converting) or original Celsius value.
    """
    if to_imperial:
        return Q_(value, "degC").to("degF").magnitude
    return value


def convert_pressure(value: float, to_imperial: bool) -> float:
    """Convert pressure between bar and psi.

    Parameters
    ----------
    value : float
        Pressure value in bar.
    to_imperial : bool
        If True, convert bar to psi. If False, return unchanged.

    Returns
    -------
    float
        Pressure in psi (if converting) or original bar value.
    """
    if to_imperial:
        return Q_(value, "bar").to("psi").magnitude
    return value


def convert_flow_rate(value: float, to_imperial: bool) -> float:
    """Convert flow rate between ml/s and fl oz/s.

    Parameters
    ----------
    value : float
        Flow rate value in milliliters per second.
    to_imperial : bool
        If True, convert ml/s to fl oz/s. If False, return unchanged.

    Returns
    -------
    float
        Flow rate in fl oz/s (if converting) or original ml/s value.
    """
    if to_imperial:
        return Q_(value, "milliliter/second").to("floz/second").magnitude
    return value


def apply_unit_conversion(data: dict, imperial: bool) -> dict:
    """Apply unit conversions to a response dict based on unit system.

    Converts known fields: dose, yield_amount, weight (g/oz),
    temperature (C/F), pressure (bar/psi), flow_rate (ml-s/floz-s),
    temp_min, temp_max, temp_step, pressure_min, pressure_max,
    saturation_flow_rate.

    Parameters
    ----------
    data : dict
        Response dictionary with metric values.
    imperial : bool
        If True, convert metric fields to imperial. If False, return unchanged.

    Returns
    -------
    dict
        Dictionary with converted values (if imperial) or original values.
    """
    if not imperial:
        return data

    weight_fields = {"dose", "yield_amount", "weight"}
    temp_fields = {"temperature", "temp_min", "temp_max", "temp_step"}
    pressure_fields = {"pressure", "pressure_min", "pressure_max"}
    flow_fields = {"flow_rate", "saturation_flow_rate"}

    result = dict(data)

    for field in weight_fields:
        if field in result and result[field] is not None:
            result[field] = round(convert_weight(result[field], True), 3)

    for field in temp_fields:
        if field in result and result[field] is not None:
            result[field] = round(convert_temperature(result[field], True), 3)

    for field in pressure_fields:
        if field in result and result[field] is not None:
            result[field] = round(convert_pressure(result[field], True), 3)

    for field in flow_fields:
        if field in result and result[field] is not None:
            result[field] = round(convert_flow_rate(result[field], True), 3)

    return result
