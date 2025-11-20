"""
Fidoo Driver Setup Configuration

Backwards-compatible setup.py for pip installation.
Modern projects should prefer pyproject.toml instead.

Usage:
    pip install .
    pip install -e .  (development mode)
"""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="fidoo-driver",
    version="1.0.0",
    author="Claude Code",
    author_email="noreply@anthropic.com",
    description="Python API driver for Fidoo Expense Management platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fidoo-driver",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/fidoo-driver/issues",
        "Documentation": "https://github.com/yourusername/fidoo-driver#readme",
        "Source Code": "https://github.com/yourusername/fidoo-driver.git",
    },
    packages=find_packages(where="."),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0,<8.0.0",
            "pytest-cov>=3.0.0,<4.0.0",
            "black>=22.0.0,<23.0.0",
            "flake8>=4.0.0,<5.0.0",
            "mypy>=0.950,<1.0.0",
            "python-dotenv>=0.20.0,<1.0.0",
        ],
    },
    keywords=[
        "fidoo",
        "expense-management",
        "api-driver",
        "corporate-cards",
        "integration",
    ],
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)
