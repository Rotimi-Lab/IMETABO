from abc import ABC, abstractmethod
import re


class Validator(ABC):
    """
    Abstract base class for all validators.
    """

    @abstractmethod
    def validate(self, value) -> bool:
        pass


class RangeValidator(Validator):
    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value) -> bool:
        return self.min_value <= value <= self.max_value


class TypeValidator(Validator):
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def validate(self, value) -> bool:
        return isinstance(value, self.expected_type)


class PatternValidator(Validator):
    def __init__(self, regex):
        self.regex = regex

    def validate(self, value) -> bool:
        if not isinstance(value, str):
            return False
        return re.fullmatch(self.regex, value) is not None


def run_all(validators: list, value) -> bool:
    """
    Returns True only if all validators pass.
    """
    for validator in validators:
        if not validator.validate(value):
            return False
    return True
