#!/usr/bin/env python3
"""
Benchmark script for NanoSimLab performance testing.

This script runs various simulation benchmarks to measure performance
and help optimize the codebase.
"""

import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from nanosimlab.analysis import msd, rdf
from nanosimlab.potentials import LennardJones, Yukawa
from nanosimlab.system import BDSimulation


def benchmark_simulation(n_particles, steps, dt=1e-4):
    """Benchmark basic simulation performance."""
    print(f"Benchmarking {n_particles} particles, {steps} steps...")

    sim = BDSimulation(
        n=n_particles,
        box=20.0,
        potential=LennardJones(epsilon=1.0, sigma=1.0, rcut=2.5),
        seed=42
    )

    start_time = time.time()
    traj = sim.run(steps=steps, dt=dt, save_every=steps//10)
    end_time = time.time()

    elapsed = end_time - start_time
    steps_per_second = steps / elapsed

    print(f"  Time: {elapsed:.2f}s")
    print(f"  Performance: {steps_per_second:.0f} steps/s")
    print(f"  Memory: {traj['positions'].nbytes / 1e6:.1f} MB")

    return elapsed, steps_per_second


def benchmark_potentials():
    """Benchmark different potential calculations."""
    print("Benchmarking potential calculations...")

    # Test data
    n_pairs = 10000
    r = np.random.uniform(0.8, 3.0, n_pairs)
    r_vec = np.random.randn(n_pairs, 3)
    r_vec = (r_vec.T / np.linalg.norm(r_vec, axis=1)).T * r[:, np.newaxis]

    potentials = {
        "Lennard-Jones": LennardJones(epsilon=1.0, sigma=1.0, rcut=2.5),
        "Yukawa": Yukawa(A=1.0, kappa=1.0, rcut=5.0)
    }

    results = {}

    for name, potential in potentials.items():
        # Warm-up
        for _ in range(10):
            potential.force(r_vec, r)

        # Benchmark
        start_time = time.time()
        for _ in range(100):
            forces = potential.force(r_vec, r)
            energies = potential.energy(r)
        end_time = time.time()

        elapsed = end_time - start_time
        results[name] = elapsed

        print(f"  {name}: {elapsed:.3f}s (100 iterations)")

    return results


def benchmark_analysis():
    """Benchmark analysis function performance."""
    print("Benchmarking analysis functions...")

    # Generate test trajectory
    T, N, dim = 1000, 200, 3
    box = 20.0

    positions = np.random.uniform(0, box, (T, N, dim))
    times = np.linspace(0, 10, T)

    # Benchmark MSD
    start_time = time.time()
    t_msd, msd_vals = msd(positions, times, box=box)
    msd_time = time.time() - start_time

    # Benchmark RDF
    start_time = time.time()
    r_vals, g_vals = rdf(positions, box=box)
    rdf_time = time.time() - start_time

    print(f"  MSD calculation: {msd_time:.3f}s")
    print(f"  RDF calculation: {rdf_time:.3f}s")

    return {"msd": msd_time, "rdf": rdf_time}


def scaling_benchmark():
    """Test performance scaling with system size."""
    print("Running scaling benchmark...")

    particle_counts = [50, 100, 200, 400, 800]
    times = []

    for n in particle_counts:
        elapsed, _ = benchmark_simulation(n, steps=1000, dt=1e-4)
        times.append(elapsed)

    # Plot results
    plt.figure(figsize=(10, 6))
    plt.subplot(1, 2, 1)
    plt.plot(particle_counts, times, 'bo-')
    plt.xlabel('Number of Particles')
    plt.ylabel('Time (seconds)')
    plt.title('Simulation Time vs System Size')
    plt.grid(True)

    # Expected O(N^2) scaling for pairwise interactions
    expected_times = times[0] * np.array(particle_counts)**2 / particle_counts[0]**2
    plt.plot(particle_counts, expected_times, 'r--', label='O(N²) scaling')
    plt.legend()

    # Performance per particle
    plt.subplot(1, 2, 2)
    perf_per_particle = [1000 / t / n for t, n in zip(times, particle_counts)]
    plt.plot(particle_counts, perf_per_particle, 'go-')
    plt.xlabel('Number of Particles')
    plt.ylabel('Steps per Second per Particle')
    plt.title('Performance per Particle')
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('benchmark_results.png', dpi=150)
    print("Saved scaling benchmark plot to benchmark_results.png")

    return particle_counts, times


def main():
    """Run all benchmarks."""
    print("="*60)
    print("NanoSimLab Performance Benchmark")
    print("="*60)

    # System info
    print(f"NumPy version: {np.__version__}")
    print(f"Platform: {Path(__file__).parent.parent}")
    print()

    # Run benchmarks
    benchmark_simulation(100, 5000)
    print()

    benchmark_potentials()
    print()

    benchmark_analysis()
    print()

    scaling_benchmark()

    print("\nBenchmark complete!")


if __name__ == "__main__":
    main()
