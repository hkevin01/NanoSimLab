"""
Pair potential implementations for nanoparticle interactions.

This module provides various potential energy functions commonly used in
nanoparticle simulations, including Lennard-Jones and Yukawa potentials.
"""

from __future__ import annotations

import numpy as np
from typing import Union


class PairPotential:
    """Base class for pair potential implementations."""
    
    def force(self, r_vec: np.ndarray, r: np.ndarray) -> np.ndarray:
        """
        Compute force between particle pairs.
        
        Args:
            r_vec: Displacement vectors between pairs (M, dim)
            r: Distances between pairs (M,)
            
        Returns:
            Forces on each pair (M, dim)
        """
        raise NotImplementedError
        
    def energy(self, r: np.ndarray) -> np.ndarray:
        """
        Compute potential energy between particle pairs.
        
        Args:
            r: Distances between pairs (M,)
            
        Returns:
            Potential energies (M,)
        """
        raise NotImplementedError


class LennardJones(PairPotential):
    """
    Lennard-Jones 12-6 potential: U(r) = 4ε[(σ/r)^12 - (σ/r)^6].
    
    Commonly used for modeling van der Waals interactions between
    nanoparticles and neutral atoms/molecules.
    """
    
    def __init__(
        self, 
        epsilon: float = 1.0, 
        sigma: float = 1.0, 
        rcut: Union[float, None] = 2.5
    ):
        """
        Initialize Lennard-Jones potential parameters.
        
        Args:
            epsilon: Energy scale parameter
            sigma: Length scale parameter  
            rcut: Cutoff radius (None for no cutoff)
        """
        self.eps = float(epsilon)
        self.sigma = float(sigma)
        self.rcut = float(rcut) if rcut is not None else None

    def _mask(self, r: np.ndarray) -> np.ndarray:
        """Apply cutoff mask to distances."""
        if self.rcut is None:
            return np.ones_like(r, dtype=bool)
        return r < self.rcut

    def force(self, r_vec: np.ndarray, r: np.ndarray) -> np.ndarray:
        """Compute Lennard-Jones forces."""
        mask = self._mask(r) & (r > 0)
        invr = np.zeros_like(r)
        invr[mask] = 1.0 / r[mask]
        sr = self.sigma * invr
        sr6 = sr**6
        sr12 = sr6**2
        # F = -dU/dr * r_vec/r = 24ε/r * (2(σ/r)^12 - (σ/r)^6) * r_vec/r
        mag = 24 * self.eps * invr * (2 * sr12 - sr6) * invr**2
        mag[~mask] = 0.0
        return (r_vec.T * mag).T

    def energy(self, r: np.ndarray) -> np.ndarray:
        """Compute Lennard-Jones potential energy."""
        mask = self._mask(r) & (r > 0)
        sr = np.zeros_like(r)
        sr[mask] = self.sigma / r[mask]
        sr6 = sr**6
        sr12 = sr6**2
        U = 4 * self.eps * (sr12 - sr6)
        U[~mask] = 0.0
        return U


class Yukawa(PairPotential):
    """
    Yukawa/screened Coulomb potential: U(r) = A * exp(-κr) / r.
    
    Models screened electrostatic interactions, commonly used for
    charged nanoparticles in ionic solutions (DLVO theory).
    """
    
    def __init__(
        self, 
        A: float = 1.0, 
        kappa: float = 1.0, 
        rcut: Union[float, None] = None
    ):
        """
        Initialize Yukawa potential parameters.
        
        Args:
            A: Interaction strength
            kappa: Inverse screening length
            rcut: Cutoff radius (None for no cutoff)
        """
        self.A = float(A)
        self.kappa = float(kappa)
        self.rcut = float(rcut) if rcut is not None else None

    def _mask(self, r: np.ndarray) -> np.ndarray:
        """Apply cutoff mask to distances.""" 
        if self.rcut is None:
            return r > 0
        return (r > 0) & (r < self.rcut)

    def force(self, r_vec: np.ndarray, r: np.ndarray) -> np.ndarray:
        """Compute Yukawa forces."""
        mask = self._mask(r)
        invr = np.zeros_like(r)
        invr[mask] = 1.0 / r[mask]
        expkr = np.zeros_like(r)
        expkr[mask] = np.exp(-self.kappa * r[mask])
        # dU/dr = A * (-κ * exp(-κr)/r - exp(-κr)/r^2)
        dUdr = np.zeros_like(r)
        dUdr[mask] = self.A * (
            -self.kappa * expkr[mask] * invr[mask] 
            - expkr[mask] * invr[mask]**2
        )
        mag = -dUdr / np.where(r > 0, r, 1.0)  # F = -dU/dr * r_vec/r
        return (r_vec.T * mag).T

    def energy(self, r: np.ndarray) -> np.ndarray:
        """Compute Yukawa potential energy."""
        mask = self._mask(r)
        invr = np.zeros_like(r)
        invr[mask] = 1.0 / r[mask]
        U = np.zeros_like(r)
        U[mask] = self.A * np.exp(-self.kappa * r[mask]) * invr[mask]
        return U
