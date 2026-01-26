from validators import (
    RangeValidator,
    TypeValidator,
    PatternValidator,
    run_all
)

def test_range_validator_passes():
    v = RangeValidator(1, 10)
    assert v.validate(5) is True

def test_range_validator_fails():
    v = RangeValidator(1, 10)
    assert v.validate(20) is False

def test_type_validator():
    v = TypeValidator(int)
    assert v.validate(5) is True
    assert v.validate("5") is False

def test_pattern_validator():
    v = PatternValidator(r"^\d+$")
    assert v.validate("123") is True
    assert v.validate("abc") is False

def test_run_all_with_mixed_validators():
    validators = [
        RangeValidator(1, 10),
        TypeValidator(int)
    ]
    assert run_all(validators, 5) is True
    assert run_all(validators, 20) is False
