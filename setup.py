from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="autotest",  # Your package name
    use_scm_version=True,  # Use setuptools-scm to handle versioning
    # version = "1.1.2",
    use_scm_version={"local_scheme": "no-local-version"},
    # Avoid using local versions
    setup_requires=[
        "setuptools>=42",
        "setuptools-scm",
    ],  # Use attr to get the version from your package
    description="""An open-source Generative AI (GenAI) application designed to 
                generate automated test cases and python Selenium scripts after dynamically 
                analysing the web-page using large language models (LLMs). An AI-driven testing tool which leverages AI and machine learning 
                for test case generation, test script optimization, and automated test execution.""",
    author="Mindfire Digital LLP",
    author_email="ankit.s@mindfiresolutions.com",
    packages=find_packages(
        where="."
    ),  # Specifies that packages are in the root directory
    package_dir={"": "."},  # Root directory is the package directory
    long_description=long_description,
    long_description_content_type="text/markdown",  # or "text/x-rst" if using reStructuredText
    install_requires=[
        "selenium==4.15.2",
        "webdriver-manager==4.0.2",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "langchain",
        "langchain_openai",
        "langchain_groq",
        "langchain_google_genai",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)