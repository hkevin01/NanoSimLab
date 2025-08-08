# Contributing to NanoSimLab

Thank you for your interest in contributing to NanoSimLab! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of Brownian dynamics or nanoparticle simulations (helpful but not required)

### Areas for Contribution

We welcome contributions in several areas:

- **Core Algorithm Development**: Improve simulation algorithms and numerical methods
- **New Features**: Add new potential functions, analysis tools, or integrators
- **Performance Optimization**: Optimize critical computational kernels
- **Documentation**: Improve user guides, API documentation, and examples
- **Testing**: Add unit tests, integration tests, and benchmarks
- **Bug Fixes**: Fix reported issues and edge cases
- **Educational Content**: Create tutorials and example notebooks

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/NanoSimLab.git
cd NanoSimLab
```

### 2. Set up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,analysis,viz]"

# Install pre-commit hooks
pre-commit install
```

### 3. Verify Installation

```bash
# Run basic tests
pytest tests/test_basic.py -v

# Test CLI
nanosim simulate --n 10 --steps 100 --out test.npz
nanosim analyze --traj test.npz
```

## Making Changes

### Workflow

1. **Create a Branch**: `git checkout -b feature/your-feature-name`
2. **Make Changes**: Implement your feature or fix
3. **Test Changes**: Run tests and ensure they pass
4. **Commit Changes**: Use clear, descriptive commit messages
5. **Push Changes**: `git push origin feature/your-feature-name`
6. **Submit Pull Request**: Open a PR with detailed description

### Coding Standards

#### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for automatic formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 100 characters

#### Naming Conventions

- **Variables and functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Modules**: `lowercase` or `snake_case`

#### Type Hints

- Use type hints for all public functions and methods
- Import types from `typing` module when needed
- Use `from __future__ import annotations` for forward references

```python
from __future__ import annotations
from typing import Optional, List, Tuple

def simulate_particles(
    n_particles: int,
    time_step: float,
    total_time: float,
    potential: Optional[PairPotential] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """Simulate particle dynamics."""
    pass
```

#### Documentation

- Use Google-style docstrings for all public functions and classes
- Include examples in docstrings when helpful
- Document parameters, return values, and exceptions

```python
def compute_rdf(positions: np.ndarray, box_size: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute radial distribution function from particle positions.

    Args:
        positions: Particle positions array (T, N, dim)
        box_size: Size of periodic simulation box

    Returns:
        Tuple of (r_values, g_values) for RDF

    Raises:
        ValueError: If positions array has incorrect shape

    Example:
        >>> positions = np.random.rand(100, 50, 3) * 10
        >>> r, g = compute_rdf(positions, box_size=10.0)
        >>> print(f"First peak at r={r[np.argmax(g)]:.2f}")
    """
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_potentials.py -v

# Run with coverage
pytest --cov=nanosimlab --cov-report=html

# Run only fast tests (exclude slow integration tests)
pytest -m "not slow"
```

### Writing Tests

- Write tests for all new functions and classes
- Use descriptive test names that explain what is being tested
- Include edge cases and error conditions
- Use fixtures for reusable test data

```python
import pytest
import numpy as np
from nanosimlab.potentials import LennardJones

class TestLennardJones:
    """Test Lennard-Jones potential implementation."""

    @pytest.fixture
    def lj_potential(self):
        """Create standard LJ potential for testing."""
        return LennardJones(epsilon=1.0, sigma=1.0, rcut=2.5)

    def test_energy_at_minimum(self, lj_potential):
        """Test that energy minimum occurs at r = 2^(1/6) * sigma."""
        r_min = 2**(1/6)
        r = np.array([r_min])
        energy = lj_potential.energy(r)
        assert energy[0] == pytest.approx(-1.0, abs=1e-10)

    def test_force_at_minimum(self, lj_potential):
        """Test that force is zero at energy minimum."""
        r_min = 2**(1/6)
        r_vec = np.array([[r_min, 0.0, 0.0]])
        r = np.array([r_min])
        force = lj_potential.force(r_vec, r)
        assert np.allclose(force, 0.0, atol=1e-10)
```

### Performance Testing

For performance-critical code, include benchmarks:

```python
def test_simulation_performance():
    """Benchmark simulation performance."""
    sim = BDSimulation(n=1000, box=20.0)

    import time
    start = time.time()
    sim.run(steps=1000, dt=1e-4, save_every=0)  # Don't save trajectory
    elapsed = time.time() - start

    # Should complete 1000 steps in reasonable time
    assert elapsed < 30.0  # 30 seconds max
```

## Documentation

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
cd docs/
make html

# View documentation
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
```

### Documentation Guidelines

- Keep documentation up-to-date with code changes
- Include practical examples and use cases
- Use clear, concise language
- Add diagrams and visualizations when helpful

## Pull Request Process

### Before Submitting

1. **Ensure tests pass**: `pytest`
2. **Check code style**: `black --check src/ tests/`
3. **Check imports**: `isort --check-only src/ tests/`
4. **Type check**: `mypy src/nanosimlab`
5. **Update documentation** if needed

### PR Description Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

## Related Issues
Closes #XXX
```

### Review Process

- All PRs require at least one reviewer approval
- Automated checks must pass (CI/CD, linting, tests)
- Address all reviewer feedback before merging
- Squash commits when merging to maintain clean history

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

### Release Checklist

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch: `git checkout -b release/vX.Y.Z`
4. Run full test suite
5. Create PR to main branch
6. After merge, create GitHub release with tag
7. Automated CI will publish to PyPI

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: [kevin@example.com](mailto:kevin@example.com) for direct contact

## Recognition

Contributors will be acknowledged in:
- `CONTRIBUTORS.md` file
- GitHub contributors list
- Release notes for significant contributions
- Academic publications when appropriate

Thank you for contributing to NanoSimLab! 🔬🤖
