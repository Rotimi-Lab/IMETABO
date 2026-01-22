# Python Naming Conventions

This document defines naming conventions for the IMETABO project, following [PEP 8](https://www.python.org/dev/peps/pep-0008/) (Python Enhancement Proposal 8) — the official Python style guide for code.

## Table of Contents
- [Files](#files)
- [Classes](#classes)
- [Functions & Methods](#functions--methods)
- [Variables](#variables)
- [Constants](#constants)
- [Private & Protected Members](#private--protected-members)
- [Examples](#examples)

---

## Files

**Convention:** `snake_case`

- Use lowercase letters separated by underscores
- Be descriptive and concise
- Avoid abbreviations unless universally understood

**Examples:**
```
data_processing.py    ✓
utils.py              ✓
csv_parser.py         ✓

DataProcessing.py     ✗
data-processing.py    ✗
dp.py                 ✗
```

**Rationale:** File names in lowercase are more portable across operating systems and consistent with Unix conventions.

---

## Classes

**Convention:** `PascalCase` (CapWords)

- Start with an uppercase letter
- Use a noun or noun phrase
- Each word capitalized without underscores
- Avoid abbreviations in class names

**Examples:**
```python
class DataProcessor:      ✓
class MetaboliteAnalyzer: ✓
class CSVReader:          ✓

class data_processor:     ✗
class processData:        ✗
class DP:                 ✗
```

**Rationale:** PascalCase for classes makes them visually distinct from functions and follows Python convention for type names.

---

## Functions & Methods

**Convention:** `snake_case`

- Use lowercase letters separated by underscores
- Use verbs or verb phrases for actions
- Be descriptive about what the function does
- Private methods: prefix with single underscore `_`
- Dunder methods: double underscore `__` (e.g., `__init__`, `__str__`)

**Examples:**
```python
def calculate_mean():            ✓
def process_metabolite_data():   ✓
def _validate_input():           ✓ (private helper)
def __init__(self):              ✓ (special method)

def CalculateMean():             ✗
def calculate_mean_v2():         ✗ (use versioning elsewhere)
def calcMean():                  ✗
```

**Rationale:** Lowercase with underscores is readable and clearly distinguishes functions from classes.

---

## Variables

**Convention:** `snake_case`

- Use lowercase letters separated by underscores
- Use meaningful, descriptive names
- Avoid single letters except for loop counters and mathematical indices
- Avoid ambiguous abbreviations

**Examples:**
```python
metabolite_concentration = 0.5       ✓
sample_count = 100                   ✓
for i in range(10):                  ✓ (loop counter acceptable)
temp = data[0]                       ✓ (temporary variable acceptable)

metaboliteConcentration = 0.5        ✗
met_conc = 0.5                       ✗ (too abbreviated)
x = data[0]                          ✗ (unclear purpose)
```

**Rationale:** Descriptive names improve code readability and reduce bugs from misunderstanding variable purpose.

---

## Constants

**Convention:** `UPPER_SNAKE_CASE`

- Use uppercase letters separated by underscores
- Define at module level
- Use for values that should never change during program execution

**Examples:**
```python
MAX_ITERATIONS = 1000                ✓
DEFAULT_SAMPLE_SIZE = 50             ✓
PI = 3.14159265359                   ✓

max_iterations = 1000                ✗
MaxIterations = 1000                 ✗
```

**Rationale:** UPPER_SNAKE_CASE immediately signals that a value is a constant and should not be modified.

---

## Private & Protected Members

**Convention:** Prefix with underscore(s)

- **Single underscore `_`**: Internal use (weak convention)
- **Double underscore `__`**: Name mangling for private members (strong convention)
- Rarely needed in Python; prefer single underscore for most cases

**Examples:**
```python
class MetaboliteData:
    def __init__(self):
        self.public_data = []           ✓ (public)
        self._internal_cache = {}       ✓ (internal, discourage access)
        self.__private_value = None     ✓ (strongly private, name-mangled)
    
    def process_data(self):             ✓ (public method)
        self._validate()                ✓ (internal method)
    
    def _validate(self):                ✓ (internal helper)
        pass
```

**Rationale:** Underscores communicate intent to other developers while remaining Pythonic (Python relies on convention rather than enforcement).

---

## Examples

### Complete File Example

```python
"""Module for processing metabolite concentration data."""

# Constants
DEFAULT_THRESHOLD = 0.01
MAX_SAMPLE_SIZE = 10000

class MetaboliteProcessor:
    """Processes and analyzes metabolite data."""
    
    def __init__(self, sample_name: str):
        """Initialize the processor with a sample name."""
        self.sample_name = sample_name
        self._data_cache = {}
    
    def load_data(self, file_path: str) -> list:
        """Load metabolite data from a CSV file."""
        metabolite_list = []
        # implementation
        return metabolite_list
    
    def _validate_concentration(self, value: float) -> bool:
        """Check if concentration is within acceptable range (private)."""
        return value >= DEFAULT_THRESHOLD
    
    def calculate_statistics(self) -> dict:
        """Calculate mean, median, and standard deviation."""
        statistics = {}
        # implementation
        return statistics


def format_output(data: dict) -> str:
    """Format processed data for display."""
    output_string = ""
    # implementation
    return output_string
```

---

## Quick Reference Table

| Item | Convention | Example |
|------|-----------|---------|
| Files | `snake_case` | `data_processor.py` |
| Classes | `PascalCase` | `class MetaboliteAnalyzer:` |
| Functions | `snake_case` | `def process_samples():` |
| Variables | `snake_case` | `sample_count = 100` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_ITERATIONS = 1000` |
| Private Methods | `_snake_case` | `def _validate():` |
| Dunder Methods | `__name__` | `def __init__(self):` |

---

## Additional Best Practices

1. **Be Descriptive**: Choose names that clearly indicate purpose
   - `calculate_mean()` ✓ vs `cm()` ✗

2. **Avoid Redundancy**: Don't repeat information
   - `class UserData:` ✓ vs `class UserDataClass:` ✗

3. **Use Type Hints**: Clarify expected types (Python 3.5+)
   ```python
   def process_data(file_path: str, threshold: float) -> list:
       """Process data above the given threshold."""
       pass
   ```

4. **Keep Names Short but Clear**: Balance brevity with readability
   - `db_connection` ✓ vs `database_connection_instance` ✗

5. **Avoid Ambiguous Abbreviations**: Use common ones sparingly
   - `config` ✓, `cfg` ✓ vs `conf` ✗

---

## References

- [PEP 8 – Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 – Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Real Python: PEP 8 Style Guide](https://realpython.com/python-pep8/)
