"""SPADE_LLM setup script."""

from setuptools import setup, find_packages
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# Get the long description from the README file
README = (HERE / "README.md").read_text()

# Import version
about = {}
with open(HERE / "spade_llm" / "version.py") as f:
    exec(f.read(), about)

setup(
    name="spade_llm",
    version=about["__version__"],
    description="Extension for SPADE to integrate Large Language Models in agents",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/spade_llm",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "spade>=3.2.0",
        # Add other dependencies based on the LLM providers you want to support
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
