from setuptools import setup, find_packages
import os

# Read requirements
def read_requirements():
    with open('requirements.txt') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read README
def read_readme():
    if os.path.exists('README.md'):
        with open('README.md', encoding='utf-8') as f:
            return f.read()
    return ""

setup(
    name="autotest-web-generator",
    version="1.0.0",
    author="Ankit Saha",  
    author_email="ankit.s@mindfiresolutions.com",
    description="Automated Web Testing Framework with LLM Integration",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/autotest-package",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        'dev': ['pytest', 'pytest-cov', 'black', 'flake8'],
    },
    include_package_data=True,
    package_data={
        'autotest': ['config/*.yaml', 'config/*.json'],
    },
    entry_points={
        'console_scripts': [
            'autotest-cli=autotest.cli.main:main',
        ],
    },
)