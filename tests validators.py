{
 "cells": [
  {
   "cell_type": "code",
   "id": "initial_id",
   "metadata": {
    "collapsed": true,
    "ExecuteTime": {
     "end_time": "2026-01-26T14:02:22.812158700Z",
     "start_time": "2026-01-26T14:02:22.778790100Z"
    }
   },
   "source": [
    "from abc import ABC, abstractmethod\n",
    "import re\n",
    "\n",
    "\n",
    "class Validator(ABC):\n",
    "    \"\"\"\n",
    "    Abstract base class for all validators.\n",
    "    \"\"\"\n",
    "\n",
    "    @abstractmethod\n",
    "    def validate(self, value) -> bool:\n",
    "        pass\n",
    "\n",
    "\n",
    "class RangeValidator(Validator):\n",
    "    def __init__(self, min_value, max_value):\n",
    "        self.min_value = min_value\n",
    "        self.max_value = max_value\n",
    "\n",
    "    def validate(self, value) -> bool:\n",
    "        return self.min_value <= value <= self.max_value\n",
    "\n",
    "\n",
    "class TypeValidator(Validator):\n",
    "    def __init__(self, expected_type):\n",
    "        self.expected_type = expected_type\n",
    "\n",
    "    def validate(self, value) -> bool:\n",
    "        return isinstance(value, self.expected_type)\n",
    "\n",
    "\n",
    "class PatternValidator(Validator):\n",
    "    def __init__(self, regex):\n",
    "        self.regex = regex\n",
    "\n",
    "    def validate(self, value) -> bool:\n",
    "        if not isinstance(value, str):\n",
    "            return False\n",
    "        return re.fullmatch(self.regex, value) is not None\n",
    "\n",
    "\n",
    "def run_all(validators: list, value) -> bool:\n",
    "    \"\"\"\n",
    "    Returns True only if all validators pass.\n",
    "    \"\"\"\n",
    "    for validator in validators:\n",
    "        if not validator.validate(value):\n",
    "            return False\n",
    "    return True\n"
   ],
   "outputs": [],
   "execution_count": 1
  },
  {
   "metadata": {
    "ExecuteTime": {
     "end_time": "2026-01-26T14:04:31.194700200Z",
     "start_time": "2026-01-26T14:04:30.753926700Z"
    }
   },
   "cell_type": "code",
   "source": [
    "from validators import (\n",
    "    RangeValidator,\n",
    "    TypeValidator,\n",
    "    PatternValidator,\n",
    "    run_all\n",
    ")\n",
    "\n",
    "\n",
    "def test_range_validator_pass():\n",
    "    validator = RangeValidator(1, 10)\n",
    "    assert validator.validate(5) is True\n",
    "\n",
    "\n",
    "def test_range_validator_fail():\n",
    "    validator = RangeValidator(1, 10)\n",
    "    assert validator.validate(15) is False\n",
    "\n",
    "\n",
    "def test_type_validator():\n",
    "    validator = TypeValidator(int)\n",
    "    assert validator.validate(3) is True\n",
    "    assert validator.validate(\"3\") is False\n",
    "\n",
    "\n",
    "def test_pattern_validator():\n",
    "    validator = PatternValidator(r\"\\d{3}\")\n",
    "    assert validator.validate(\"123\") is True\n",
    "    assert validator.validate(\"abc\") is False\n",
    "\n",
    "\n",
    "def test_run_all_with_mixed_validators():\n",
    "    validators = [\n",
    "        TypeValidator(int),\n",
    "        RangeValidator(1, 100)\n",
    "    ]\n",
    "\n",
    "    assert run_all(validators, 50) is True\n",
    "    assert run_all(validators, 150) is False\n"
   ],
   "id": "3700bbd9932ff84a",
   "outputs": [
    {
     "ename": "ImportError",
     "evalue": "cannot import name 'RangeValidator' from 'validators' (C:\\Users\\alonge mary\\PycharmProjects\\JupyterProject1\\.venv\\Lib\\site-packages\\validators\\__init__.py)",
     "output_type": "error",
     "traceback": [
      "\u001B[31m---------------------------------------------------------------------------\u001B[39m",
      "\u001B[31mImportError\u001B[39m                               Traceback (most recent call last)",
      "\u001B[36mCell\u001B[39m\u001B[36m \u001B[39m\u001B[32mIn[5]\u001B[39m\u001B[32m, line 1\u001B[39m\n\u001B[32m----> \u001B[39m\u001B[32m1\u001B[39m \u001B[38;5;28;01mfrom\u001B[39;00m\u001B[38;5;250m \u001B[39m\u001B[34;01mvalidators\u001B[39;00m\u001B[38;5;250m \u001B[39m\u001B[38;5;28;01mimport\u001B[39;00m (\n\u001B[32m      2\u001B[39m     RangeValidator,\n\u001B[32m      3\u001B[39m     TypeValidator,\n\u001B[32m      4\u001B[39m     PatternValidator,\n\u001B[32m      5\u001B[39m     run_all\n\u001B[32m      6\u001B[39m )\n\u001B[32m      9\u001B[39m \u001B[38;5;28;01mdef\u001B[39;00m\u001B[38;5;250m \u001B[39m\u001B[34mtest_range_validator_pass\u001B[39m():\n\u001B[32m     10\u001B[39m     validator = RangeValidator(\u001B[32m1\u001B[39m, \u001B[32m10\u001B[39m)\n",
      "\u001B[31mImportError\u001B[39m: cannot import name 'RangeValidator' from 'validators' (C:\\Users\\alonge mary\\PycharmProjects\\JupyterProject1\\.venv\\Lib\\site-packages\\validators\\__init__.py)"
     ]
    }
   ],
   "execution_count": 5
  },
  {
   "metadata": {
    "ExecuteTime": {
     "end_time": "2026-01-25T17:49:01.926030500Z",
     "start_time": "2026-01-25T17:49:01.798297600Z"
    }
   },
   "cell_type": "code",
   "source": "",
   "id": "f1e662a4e7c224aa",
   "outputs": [],
   "execution_count": 13
  },
  {
   "metadata": {},
   "cell_type": "code",
   "outputs": [],
   "execution_count": null,
   "source": " ",
   "id": "7dee1d033dca06fc"
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 2
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython2",
   "version": "2.7.6"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
