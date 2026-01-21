"""
Setup configuration for IMETABO.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="imetabo",
    version="0.1.0",
    author="IMETABO Contributors",
    author_email="contact@imetabo.dev",
    description="A comprehensive Python library for metabolomics data analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Rotimi-Lab/IMETABO",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        # Add your dependencies here
        # "numpy>=1.21.0",
        # "pandas>=1.3.0",
        # "scipy>=1.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.950",
            "sphinx>=4.5",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # Add CLI commands here
            # "imetabo-cli=imetabo.cli:main",
        ],
    },
)
