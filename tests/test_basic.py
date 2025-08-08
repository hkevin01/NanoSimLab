"""
Basic functionality tests for NanoSimLab.

This module provides unit tests for core simulation components
to ensure correctness and catch regressions.
"""

import numpy as np
import pytest

from nanosimlab.system import BDSimulation
from nanosimlab.potentials import LennardJones, Yukawa
from nanosimlab.analysis import msd, rdf, diffusion_coefficient


class TestPotentials:
    """Test pair potential implementations."""
    
    def test_lennard_jones_basic(self):
        """Test basic LJ potential functionality."""
        lj = LennardJones(epsilon=1.0, sigma=1.0, rcut=2.5)
        
        # Test at sigma (minimum)
        r = np.array([1.0])
        r_vec = np.array([[1.0, 0.0, 0.0]])
        
        energy = lj.energy(r)
        force = lj.force(r_vec, r)
        
        assert energy[0] == pytest.approx(-1.0, abs=1e-10)
        assert force[0, 0] == pytest.approx(0.0, abs=1e-10)
    
    def test_yukawa_basic(self):
        """Test basic Yukawa potential functionality."""
        yuk = Yukawa(A=1.0, kappa=1.0)
        
        r = np.array([1.0])
        r_vec = np.array([[1.0, 0.0, 0.0]])
        
        energy = yuk.energy(r)
        force = yuk.force(r_vec, r)
        
        expected_energy = np.exp(-1.0)
        assert energy[0] == pytest.approx(expected_energy, rel=1e-6)
        assert force.shape == (1, 3)


class TestSimulation:
    """Test simulation engine."""
    
    def test_simulation_creation(self):
        """Test basic simulation setup."""
        sim = BDSimulation(
            n=32, 
            box=10.0, 
            dim=3, 
            temperature=1.0,
            seed=42
        )
        
        assert sim.n == 32
        assert sim.dim == 3
        assert sim.box == 10.0
        assert sim.x.shape == (32, 3)
    
    def test_short_simulation(self):
        """Test running a short simulation."""
        sim = BDSimulation(
            n=16,
            box=8.0,
            dim=3,
            temperature=1.0,
            potential=LennardJones(epsilon=0.5, sigma=1.0, rcut=2.0),
            seed=123
        )
        
        traj = sim.run(steps=100, dt=1e-3, save_every=10)
        
        assert "positions" in traj
        assert "times" in traj
        assert traj["positions"].shape[0] == 11  # 100/10 + 1 for step 0
        assert traj["positions"].shape[1] == 16
        assert traj["positions"].shape[2] == 3
    
    def test_force_calculation(self):
        """Test force calculation."""
        sim = BDSimulation(
            n=2,
            box=None,  # Open boundaries
            dim=3,
            potential=LennardJones(epsilon=1.0, sigma=1.0)
        )
        
        # Place particles at specific positions
        sim.x = np.array([[0.0, 0.0, 0.0], [1.5, 0.0, 0.0]])
        
        forces = sim.compute_forces(sim.x)
        
        # Forces should be equal and opposite
        assert forces.shape == (2, 3)
        assert np.allclose(forces[0], -forces[1])


class TestAnalysis:
    """Test analysis functions."""
    
    def test_msd_calculation(self):
        """Test MSD calculation."""
        # Create simple test trajectory
        T, N, dim = 50, 10, 3
        times = np.linspace(0, 1, T)
        
        # Linear motion for easy testing
        positions = np.zeros((T, N, dim))
        for i in range(T):
            positions[i, :, 0] = times[i]  # x increases linearly
        
        t_msd, msd_vals = msd(positions, times)
        
        assert len(t_msd) == T
        assert len(msd_vals) == T
        assert msd_vals[0] == 0.0  # MSD starts at zero
        assert msd_vals[-1] > 0.0  # MSD increases
    
    def test_rdf_calculation(self):
        """Test RDF calculation."""
        # Simple 2-particle system
        T, N, dim = 10, 4, 3
        box = 5.0
        
        # Random positions
        np.random.seed(42)
        positions = np.random.uniform(0, box, (T, N, dim))
        
        r_vals, g_vals = rdf(positions, box=box, bins=20)
        
        assert len(r_vals) == 20
        assert len(g_vals) == 20
        assert np.all(r_vals >= 0)
        assert np.all(g_vals >= 0)
    
    def test_diffusion_coefficient(self):
        """Test diffusion coefficient estimation."""
        # Create MSD data with known slope
        times = np.linspace(0, 10, 100)
        true_D = 0.5
        dim = 3
        msd_vals = 2 * dim * true_D * times + 0.1 * np.random.randn(100)
        
        D_est, r2 = diffusion_coefficient(times, msd_vals, dim=dim)
        
        assert D_est == pytest.approx(true_D, rel=0.1)
        assert r2 > 0.9  # Should be good fit for linear data


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_workflow(self):
        """Test complete simulation and analysis workflow."""
        # Small but complete simulation
        sim = BDSimulation(
            n=20,
            box=6.0,
            dim=3,
            temperature=1.0,
            potential=LennardJones(epsilon=0.8, sigma=1.0, rcut=2.0),
            seed=456
        )
        
        # Run simulation
        traj = sim.run(steps=500, dt=5e-4, save_every=25)
        
        # Analyze results
        t_msd, msd_vals = msd(traj["positions"], traj["times"], 
                             box=traj["box"])
        r_vals, g_vals = rdf(traj["positions"], box=traj["box"])
        
        # Basic sanity checks
        assert len(t_msd) == traj["positions"].shape[0]
        assert msd_vals[0] == 0.0
        assert np.all(msd_vals >= 0)
        assert len(r_vals) == len(g_vals)
        assert np.all(g_vals >= 0)


if __name__ == "__main__":
    pytest.main([__file__])
