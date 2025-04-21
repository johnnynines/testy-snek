from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pydesktop-test",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A PyTest-based testing framework for Python desktop applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pydesktop-test",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: User Interfaces",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pytest>=6.0.0",
        "pytest-html>=3.0.0",
        "pytest-cov>=2.12.0",
        "pillow>=8.0.0",
        "pyyaml>=5.4.0",
        "rich>=10.0.0",
        "typer>=0.3.2",
    ],
    entry_points={
        "console_scripts": [
            "desktop-test=pydesktop_test.cli:app",
        ],
    },
)