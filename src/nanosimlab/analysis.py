"""
Analysis tools for nanoparticle simulation trajectories.

This module provides functions to compute common statistical and structural
properties from Brownian dynamics trajectories, including mean-squared
displacement and radial distribution functions.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Optional


def msd(
    positions: np.ndarray, 
    times: np.ndarray, 
    box: Optional[float] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute mean-squared displacement (MSD) from trajectory.
    
    The MSD quantifies particle diffusion and is used to determine
    diffusion coefficients via the Einstein relation: D = MSD/(2*dim*t).
    
    Args:
        positions: Trajectory positions (T, N, dim)
        times: Time points (T,)
        box: Box length for unwrapping (basic implementation)
        
    Returns:
        Tuple of (times, msd_values)
    """
    T, N, dim = positions.shape
    
    # Compute displacements from initial positions
    disp = positions - positions[0]
    
    # Basic unwrapping for periodic boundaries
    if box is not None:
        # Simple unwrapping - for small time steps this gives reasonable MSD
        disp = (disp + box/2) % box - box/2
    
    # Mean-squared displacement averaged over particles
    msd_t = (disp**2).sum(axis=2).mean(axis=1)
    
    return times, msd_t


def rdf(
    positions: np.ndarray, 
    box: float, 
    r_max: Optional[float] = None, 
    bins: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute radial distribution function g(r) from trajectory.
    
    The RDF describes the probability of finding a particle at distance r
    from a reference particle, normalized by the bulk density. It reveals
    structural ordering and phase behavior in nanoparticle systems.
    
    Args:
        positions: Trajectory positions (T, N, dim)
        box: Periodic box length
        r_max: Maximum distance (default: box/2)
        bins: Number of histogram bins
        
    Returns:
        Tuple of (r_values, g_values)
    """
    assert box is not None, "RDF calculation requires periodic boundaries"
    
    T, N, dim = positions.shape
    
    if r_max is None:
        r_max = 0.5 * box
        
    # Create histogram bins
    bin_edges = np.linspace(0, r_max, bins + 1)
    dr = bin_edges[1] - bin_edges[0]
    r = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    g = np.zeros(bins)
    
    # Accumulate histogram over all frames
    for frame in positions:
        # Compute all pairwise distances
        diffs = frame[np.newaxis, :, :] - frame[:, np.newaxis, :]
        
        # Apply minimum image convention
        diffs = diffs - box * np.round(diffs / box)
        
        # Calculate distances
        dists = np.linalg.norm(diffs, axis=2)
        
        # Extract upper triangular (unique pairs)
        iu = np.triu_indices(N, k=1)
        pair_dists = dists[iu]
        
        # Add to histogram
        hist, _ = np.histogram(pair_dists, bins=bin_edges)
        g += hist
    
    # Normalize to get g(r)
    volume = box**dim
    density = N / volume
    
    # Shell volume element
    if dim == 3:
        shell_vol = 4 * np.pi * r**2 * dr
    elif dim == 2:
        shell_vol = 2 * np.pi * r * dr
    else:
        raise ValueError("RDF only supports 2D and 3D systems")
    
    # Expected number of particles in shell (ideal gas)
    n_ideal = density * shell_vol * N * T / 2
    
    # Avoid division by zero
    n_ideal = np.where(n_ideal > 0, n_ideal, 1)
    
    g = g / n_ideal
    
    return r, g


def diffusion_coefficient(
    times: np.ndarray, 
    msd_values: np.ndarray, 
    dim: int = 3,
    fit_start: float = 0.1,
    fit_end: float = 0.8
) -> Tuple[float, float]:
    """
    Estimate diffusion coefficient from MSD using Einstein relation.
    
    Fits linear regime of MSD vs time to extract diffusion coefficient:
    MSD = 2 * dim * D * t
    
    Args:
        times: Time points
        msd_values: Mean-squared displacement values
        dim: Spatial dimensionality
        fit_start: Start of linear fitting region (fraction of total time)
        fit_end: End of linear fitting region (fraction of total time)
        
    Returns:
        Tuple of (diffusion_coefficient, r_squared)
    """
    # Select fitting region
    t_max = times[-1]
    mask = (times >= fit_start * t_max) & (times <= fit_end * t_max)
    
    if mask.sum() < 2:
        raise ValueError("Insufficient data points in fitting region")
    
    t_fit = times[mask]
    msd_fit = msd_values[mask]
    
    # Linear fit: MSD = slope * t + intercept
    coeffs = np.polyfit(t_fit, msd_fit, 1)
    slope = coeffs[0]
    
    # Diffusion coefficient from Einstein relation
    D = slope / (2 * dim)
    
    # Calculate R-squared
    msd_pred = np.polyval(coeffs, t_fit)
    ss_res = np.sum((msd_fit - msd_pred)**2)
    ss_tot = np.sum((msd_fit - np.mean(msd_fit))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return D, r_squared


def end_to_end_distance(positions: np.ndarray) -> np.ndarray:
    """
    Compute end-to-end distances for polymer-like nanostructures.
    
    Args:
        positions: Trajectory positions (T, N, dim)
        
    Returns:
        End-to-end distances for each frame (T,)
    """
    # Distance between first and last particle (polymer ends)
    end_to_end = np.linalg.norm(
        positions[:, -1, :] - positions[:, 0, :], 
        axis=1
    )
    return end_to_end
