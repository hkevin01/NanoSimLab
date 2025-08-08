# NanoSimLab

[![CI](https://github.com/hkevin01/NanoSimLab/workflows/CI/badge.svg)](https://github.com/hkevin01/NanoSimLab/actions)
[![Documentation Status](https://readthedocs.org/projects/nanosimlab/badge/?version=latest)](https://nanosimlab.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/nanosimlab.svg)](https://badge.fury.io/py/nanosimlab)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Lightweight, extensible Brownian dynamics toolkit for nanoparticles and proto-nanorobotics**

NanoSimLab provides accessible tools for simulating and analyzing nanoparticle systems using Brownian dynamics, with a focus on nanorobotics research and development. The toolkit runs out-of-the-box with NumPy/SciPy and offers seamless integration with popular computational chemistry and materials science libraries.

## 🚀 Key Features

- **🔬 Brownian Dynamics Simulations**: Overdamped Langevin integration in 2D/3D with periodic boundary conditions
- **⚗️ Multiple Pair Potentials**: Lennard-Jones, Yukawa/screened Coulomb, with extensible framework
- **📊 Built-in Analysis**: Mean-squared displacement (MSD), radial distribution function (RDF), diffusion coefficients
- **🖥️ Simple CLI**: User-friendly command-line interface for non-programmers
- **🔧 Extensible Architecture**: Optional integrations with HOOMD-blue, OpenMM, ASE, MDAnalysis, and more
- **🤖 Nanorobotics Focus**: Designed for proto-nanobot behavior and collective particle control

## 📦 Installation

### Quick Install (Recommended)
```bash
pip install nanosimlab
```

### Development Install
```bash
git clone https://github.com/hkevin01/NanoSimLab.git
cd NanoSimLab
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev,analysis,viz]"
```

### Optional Dependencies
```bash
# For advanced analysis and visualization
pip install "nanosimlab[analysis,viz]"

# For molecular simulation integration  
pip install "nanosimlab[molsim,builder]"

# For development
pip install "nanosimlab[dev]"
```

## 🏃‍♂️ Quick Start

### Command Line Interface
Run a simple nanoparticle simulation:
```bash
# Simulate 200 Lennard-Jones particles
nanosim simulate --n 200 --box 20 --steps 20000 --dt 1e-4 --temp 1.0 \
                 --potential lj --epsilon 1.0 --sigma 1.0 --rcut 2.5 \
                 --out trajectory.npz

# Analyze the results
nanosim analyze --traj trajectory.npz --rdf --msd --diffusion
```

### Python API
```python
import numpy as np
from nanosimlab.system import BDSimulation
from nanosimlab.potentials import LennardJones
from nanosimlab.analysis import msd, rdf

# Create simulation
sim = BDSimulation(
    n=200,                    # Number of particles
    box=20.0,                # Periodic box size
    dim=3,                   # 3D simulation
    temperature=1.0,         # Reduced temperature
    potential=LennardJones(epsilon=1.0, sigma=1.0, rcut=2.5)
)

# Run simulation
trajectory = sim.run(steps=10000, dt=1e-4, save_every=100)

# Analyze results
times, msd_values = msd(trajectory["positions"], trajectory["times"])
r, g_r = rdf(trajectory["positions"], box=trajectory["box"])

# Save results
np.savez("results.npz", 
         positions=trajectory["positions"],
         times=times, msd=msd_values, 
         r=r, rdf=g_r)
```

## 🎯 Use Cases

### Nanoparticle Self-Assembly
```python
from nanosimlab.potentials import Yukawa

# Simulate charged nanoparticles with screening
sim = BDSimulation(n=100, potential=Yukawa(A=5.0, kappa=1.0))
trajectory = sim.run(steps=50000, dt=5e-5)
```

### Drug Delivery Simulation
```python
# Model drug-carrier nanoparticles in biological medium
sim = BDSimulation(
    n=50, box=15.0, temperature=310/300,  # Body temperature
    potential=LennardJones(epsilon=0.5, sigma=2.0)  # Biocompatible particles
)
```

### Micro-swimmer Collective Behavior
```python
# Simulate active particles with propulsion (future feature)
# sim.add_external_field(PropulsionField(strength=2.0, direction="random"))
```

## 📚 Documentation

- **[User Guide](docs/)**: Comprehensive tutorials and examples
- **[API Reference](https://nanosimlab.readthedocs.io)**: Detailed function documentation  
- **[Examples Gallery](examples/)**: Jupyter notebooks for common use cases
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to the project

## 🔧 Project Structure

```
NanoSimLab/
├── src/nanosimlab/          # Core package source code
│   ├── __init__.py          # Package initialization
│   ├── potentials.py        # Pair potential implementations
│   ├── integrators.py       # Numerical integration schemes
│   ├── system.py            # Main simulation engine
│   ├── analysis.py          # Trajectory analysis tools
│   └── cli.py               # Command-line interface
├── tests/                   # Unit and integration tests
├── docs/                    # Documentation source files
├── scripts/                 # Utility scripts
├── data/                    # Example datasets
├── assets/                  # Images and media files
└── pyproject.toml           # Project configuration
```

## 🛠️ Development Roadmap

### Current Status (v0.1.0)
- ✅ Core Brownian dynamics engine
- ✅ Basic pair potentials (LJ, Yukawa)
- ✅ MSD and RDF analysis
- ✅ Command-line interface

### Upcoming Features (v0.2.0)
- 🔄 HOOMD-blue GPU backend
- 🔄 Advanced visualization with NGLView
- 🔄 External field support (E/M fields, flow)
- 🔄 Jupyter notebook tutorials

### Future Vision (v1.0.0)
- 📋 Machine learning integration
- 📋 Nanorobot control algorithms  
- 📋 Multi-scale modeling capabilities
- 📋 Commercial simulation package integration

## 🤝 Contributing

We welcome contributions from the research community! See our [Contributing Guide](CONTRIBUTING.md) for details on:

- Setting up development environment
- Code style and testing requirements
- Submitting pull requests
- Reporting bugs and feature requests

## 📖 Citation

If you use NanoSimLab in your research, please cite:

```bibtex
@software{nanosimlab2025,
  title={NanoSimLab: Brownian Dynamics Toolkit for Nanoparticles and Nanorobotics},
  author={Kevin},
  year={2025},
  url={https://github.com/hkevin01/NanoSimLab},
  version={0.1.0}
}
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by computational tools in the nanorobotics and materials science communities
- Built on the robust NumPy/SciPy scientific Python ecosystem
- Designed to complement existing molecular simulation frameworks

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/hkevin01/NanoSimLab/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/hkevin01/NanoSimLab/discussions)
- **Email**: [kevin@example.com](mailto:kevin@example.com)

---

*NanoSimLab: Bridging the gap between nanorobotics theory and simulation practice* 🔬🤖
