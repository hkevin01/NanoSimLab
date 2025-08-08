"""
Numerical integration schemes for Brownian dynamics simulations.

This module provides integration algorithms for overdamped Langevin dynamics,
commonly used in nanoparticle simulations where inertial effects are
negligible.
"""

from __future__ import annotations

import numpy as np
from typing import Optional


def overdamped_langevin_step(
    x: np.ndarray,
    force: np.ndarray,
    dt: float,
    temperature: float = 1.0,
    gamma: float = 1.0,
    rng: Optional[np.random.Generator] = None
) -> np.ndarray:
    """
    Perform one Euler-Maruyama integration step for overdamped Langevin
    dynamics.

    Integrates the stochastic differential equation:
    dx = (F/γ) dt + √(2kT/γ) dW

    Where F is the force, γ is friction, T is temperature, and dW is
    Wiener noise.
    Uses reduced units with Boltzmann constant k_B = 1.
    
    Args:
        x: Current positions (N, dim)
        force: Forces on particles (N, dim)
        dt: Time step
        temperature: System temperature (reduced units)
        gamma: Friction coefficient
        rng: Random number generator (creates new if None)
        
    Returns:
        New positions after one integration step (N, dim)
    """
    if rng is None:
        rng = np.random.default_rng()
    
    # Deterministic drift term
    drift = (force / gamma) * dt
    
    # Stochastic diffusion term
    sigma = np.sqrt(2.0 * temperature / gamma * dt)
    noise = rng.normal(0.0, 1.0, size=x.shape) * sigma
    
    return x + drift + noise


def velocity_verlet_step(
    x: np.ndarray,
    v: np.ndarray,
    force_func,
    dt: float,
    mass: float = 1.0
) -> tuple[np.ndarray, np.ndarray]:
    """
    Perform one velocity-Verlet integration step for Newtonian dynamics.
    
    This is included for future extension to underdamped dynamics where
    inertial effects become important (e.g., larger nanoparticles).
    
    Args:
        x: Current positions (N, dim)
        v: Current velocities (N, dim)
        force_func: Function that computes forces given positions
        dt: Time step
        mass: Particle mass
        
    Returns:
        Tuple of (new_positions, new_velocities)
    """
    # Current forces
    f_current = force_func(x)
    
    # Update positions
    x_new = x + v * dt + 0.5 * (f_current / mass) * dt**2
    
    # Compute forces at new positions
    f_new = force_func(x_new)
    
    # Update velocities
    v_new = v + 0.5 * (f_current + f_new) / mass * dt
    
    return x_new, v_new
