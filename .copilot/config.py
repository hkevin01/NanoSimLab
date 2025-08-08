"""
Configuration for GitHub Copilot in NanoSimLab.

This module contains settings and preferences for GitHub Copilot
to provide better assistance for scientific computing and nanorobotics code.
"""

# Copilot context and preferences for NanoSimLab project
COPILOT_CONTEXT = {
    "project_type": "scientific_computing",
    "domain": "nanorobotics",
    "primary_language": "python",
    "frameworks": [
        "numpy",
        "scipy",
        "matplotlib",
        "pytest",
        "click"
    ],
    "scientific_libraries": [
        "mdanalysis",
        "ase",
        "hoomd",
        "openmm",
        "pymatgen"
    ],
    "coding_style": {
        "naming_convention": "snake_case",
        "line_length": 100,
        "type_hints": True,
        "docstring_style": "google"
    },
    "preferred_patterns": [
        "numpy array operations",
        "scientific computing best practices",
        "brownian dynamics algorithms",
        "molecular simulation techniques",
        "statistical analysis methods"
    ]
}
