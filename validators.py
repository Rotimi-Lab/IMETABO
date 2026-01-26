from abc import ABC, abstractmethod
import re
from wsgiref.validate import validator


class Validator(ABC):
    @abstractmethod
    def validate(self, value) -> bool:
        pass
    
class RangeValidator(Validator):
  def __init__(self, min_value, max_value):
        self.min = min_value
        self.max = max_value

  def validate(self, value) -> bool:
        return self.min <= value <= self.max
  
class TypeValidator(Validator):
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def validate(self, value) -> bool:
        return isinstance(value, self.expected_type)
    
    class PatternValidator(Validator):
     def __init__(self, regex):
        self.regex = regex

        def validate(self, value) -> bool:
            return bool(re.match(self.regex, str(value)))
        
        def run_all(validators: list, value) -> bool:
         return all(validator.validate(value) for validator in validators)
        
         def run_all(validators: list, value) -> bool:
          for validator in validators:
           if not validator.validate(value):
            return False
         return True
        
        print("run_all loaded")

