# Data Directory

This directory contains example datasets, simulation presets, and reference data for NanoSimLab.

## Contents

### `simulation_presets.toml`
Pre-configured simulation parameters for common nanoparticle systems:
- **Gold nanoparticles**: Metallic particles in aqueous solution
- **Drug carriers**: Biocompatible nanoparticles for drug delivery
- **Magnetic particles**: Magnetite nanoparticles with dipolar interactions
- **Self-assembly**: Particles designed for controlled self-assembly

### Usage Examples

Load preset parameters in Python:
```python
import tomli
from nanosimlab.system import BDSimulation
from nanosimlab.potentials import LennardJones

# Load preset parameters
with open("data/simulation_presets.toml", "rb") as f:
    presets = tomli.load(f)

gold_params = presets["gold_nanoparticles"]

# Create simulation with preset parameters
sim = BDSimulation(
    n=gold_params["n_particles"],
    box=gold_params["box_size"],
    temperature=gold_params["temperature"],
    potential=LennardJones(
        epsilon=gold_params["epsilon"],
        sigma=gold_params["sigma"],
        rcut=gold_params["cutoff"]
    )
)
```

Use with CLI:
```bash
# Extract parameters and run simulation
nanosim simulate \
  --n 100 \
  --box 15.0 \
  --temp 1.0 \
  --steps 50000 \
  --dt 1e-4 \
  --potential lj \
  --epsilon 0.8 \
  --sigma 1.2 \
  --rcut 3.0 \
  --out gold_nanoparticles.npz
```

## File Formats

### Trajectory Files (`.npz`)
NumPy compressed archives containing:
- `positions`: Particle positions over time (T, N, dim)
- `times`: Time points (T,)
- `box`: Box size for periodic boundaries
- `dim`: Spatial dimensionality
- `n_particles`: Number of particles

### Parameter Files (`.toml`)
TOML format configuration files with simulation parameters, analysis settings, and metadata.

## Data Organization

```
data/
├── README.md                    # This file
├── simulation_presets.toml      # Pre-configured parameters
├── examples/                    # Example trajectories and datasets
│   ├── small_system.npz        # Quick test case
│   └── benchmarks/             # Performance benchmark data
├── reference/                   # Reference data and validation
│   ├── literature_data/        # Published simulation results
│   └── experimental/           # Experimental comparison data
└── processed/                   # Analysis results and derived data
    ├── rdf_data/               # Radial distribution functions
    └── msd_fits/               # Mean-squared displacement fits
```

## Adding New Data

When adding new datasets:

1. **Documentation**: Include a brief description and source
2. **Metadata**: Add relevant parameters and conditions
3. **Format**: Use standard NumPy `.npz` or TOML formats
4. **Size**: Keep files under 100MB (use Git LFS for larger files)
5. **Licensing**: Ensure proper attribution for external data

## Data Sources

- **Simulation presets**: Based on typical literature values for nanoparticle systems
- **Reference data**: Compiled from peer-reviewed publications
- **Benchmark data**: Generated using validated simulation codes

## Notes

- All simulation parameters use reduced units unless otherwise specified
- Temperature is given in units of kT (thermal energy)
- Distances are in units of particle diameter
- Time is in units of τ = σ√(m/ε) for Lennard-Jones systems
