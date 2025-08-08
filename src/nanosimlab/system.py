"""
Core system classes for Brownian dynamics simulations.

This module provides the main simulation engine for nanoparticle systems,
including boundary conditions, force calculations, and trajectory management.
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Dict, Any, Callable
from .integrators import overdamped_langevin_step


def minimum_image_displacement(dx: np.ndarray, box: float) -> np.ndarray:
    """
    Apply minimum image convention for periodic boundary conditions.
    
    Args:
        dx: Displacement vectors
        box: Box length (cubic box assumed)
        
    Returns:
        Corrected displacement vectors
    """
    if box is None:
        return dx
    return dx - box * np.round(dx / box)


class BDSimulation:
    """
    Brownian dynamics simulation engine for nanoparticle systems.
    
    This class handles the main simulation loop, including force calculations,
    integration, and trajectory storage for nanoparticle ensembles.
    """
    
    def __init__(
        self,
        n: int = 100,
        box: Optional[float] = 20.0,
        dim: int = 3,
        temperature: float = 1.0,
        gamma: float = 1.0,
        potential=None,
        seed: Optional[int] = None
    ):
        """
        Initialize Brownian dynamics simulation.
        
        Args:
            n: Number of particles
            box: Periodic box length (None for open boundaries)
            dim: Spatial dimensionality (2 or 3)
            temperature: System temperature (reduced units, k_B=1)
            gamma: Friction coefficient
            potential: Pair potential object
            seed: Random seed for reproducibility
        """
        assert dim in (2, 3), "Dimensionality must be 2 or 3"
        self.n = int(n)
        self.dim = int(dim)
        self.box = float(box) if box is not None else None
        self.temperature = float(temperature)
        self.gamma = float(gamma)
        self.potential = potential
        self.rng = np.random.default_rng(seed)
        
        # Initialize particle positions
        self.x = self._random_positions()

    def _random_positions(self) -> np.ndarray:
        """Generate random initial positions avoiding severe overlaps."""
        if self.box is None:
            return self.rng.uniform(-5, 5, size=(self.n, self.dim))
        return self.rng.uniform(0, self.box, size=(self.n, self.dim))

    def _pair_deltas(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, 
                                                  np.ndarray, np.ndarray]:
        """
        Compute pairwise displacements and distances.
        
        Args:
            x: Particle positions (N, dim)
            
        Returns:
            Tuple of (displacement_vectors, distances, i_indices, j_indices)
        """
        # Upper triangular indices for unique pairs
        idx_i, idx_j = np.triu_indices(self.n, k=1)
        r_vec = x[idx_j] - x[idx_i]
        
        if self.box is not None:
            r_vec = minimum_image_displacement(r_vec, self.box)
            
        r = np.linalg.norm(r_vec, axis=1)
        return r_vec, r, idx_i, idx_j

    def compute_forces(self, x: np.ndarray) -> np.ndarray:
        """
        Compute total forces on all particles.
        
        Args:
            x: Particle positions (N, dim)
            
        Returns:
            Forces on each particle (N, dim)
        """
        r_vec, r, i_idx, j_idx = self._pair_deltas(x)
        
        if self.potential is None:
            F_pairs = np.zeros_like(r_vec)
        else:
            F_pairs = self.potential.force(r_vec, r)
        
        # Accumulate pairwise forces: F_i += F_ij, F_j -= F_ij
        F = np.zeros_like(x)
        np.add.at(F, i_idx, F_pairs)
        np.add.at(F, j_idx, -F_pairs)
        
        return F

    def _apply_pbc(self, x: np.ndarray) -> np.ndarray:
        """Apply periodic boundary conditions to positions."""
        if self.box is None:
            return x
        return x % self.box

    def run(
        self,
        steps: int = 10000,
        dt: float = 1e-4,
        save_every: int = 100,
        callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run Brownian dynamics simulation.
        
        Args:
            steps: Number of integration steps
            dt: Time step size
            save_every: Save trajectory every N steps (0 to disable)
            callback: Optional callback function called each step
            
        Returns:
            Dictionary containing trajectory data
        """
        positions = []
        times = []
        x = self.x.copy()
        
        for t in range(steps):
            # Compute forces
            F = self.compute_forces(x)
            
            # Integration step
            x = overdamped_langevin_step(
                x, F, dt, 
                temperature=self.temperature,
                gamma=self.gamma,
                rng=self.rng
            )
            
            # Apply boundary conditions
            x = self._apply_pbc(x)
            
            # Save trajectory
            if save_every and (t % save_every == 0):
                positions.append(x.copy())
                times.append(t * dt)
                
            # User callback
            if callback is not None:
                callback(t, x, F)
        
        positions = np.array(positions)  # (frames, N, dim)
        times = np.array(times)
        
        # Update internal state
        self.x = x
        
        return {
            "positions": positions,
            "times": times,
            "box": self.box,
            "dim": self.dim,
            "n_particles": self.n
        }
