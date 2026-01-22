# Getting Started with IMETABO

This guide will help you get started with developing IMETABO.

## Installation for Development

1. Clone the repository:
   ```bash
   git clone https://github.com/Rotimi-Lab/IMETABO.git
   cd IMETABO
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=imetabo
```

## Code Style

Format code with Black:
```bash
black imetabo tests
```

Lint with flake8:
```bash
flake8 imetabo tests
```

Type checking with mypy:
```bash
mypy imetabo
```

## Project Structure

```
IMETABO/
├── imetabo/           # Main package
│   ├── __init__.py
│   ├── core.py        # Core functionality
│   └── utils.py       # Utility functions
├── tests/             # Test suite
├── docs/              # Documentation
├── examples/          # Example scripts
├── setup.py           # Setup configuration
├── pyproject.toml     # Project metadata
└── README.md          # Project README
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.
