# AUTOTEST: Automated test case and Selenium script generation using LLM 

<img src="./autotest_image.jpg" alt="Project Logo" width="100" height="auto"> <!-- Include a project logo or banner here, if applicable -->


## Table of Contents

- [Project Name](#project-name)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Features](#features)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [Future Scope and Improvements](#future-scope-and-improvements)
  - [New features](#new-features)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Description

An open-source Generative AI (GenAI) application designed to generate automated test cases and python Selenium scripts after dynamically analyzing the web-page using large language models (LLMs). AI-driven testing tool which leverages AI and machine learning for test case generation, test script optimization, and automated test execution. This application serves as an testing automation tool which performs recursive unique internal url extraction from the base url with BFS upto a specified depth. Then analyze each page to extract the page metadata, generate page specific test cases and executable python selenium scripts. The valid set of data inputs required to test page authentication functionalities like login or registration can be provided in the ``auth_test_data.json`` file. This automation tool will generate comprehensive suite of test cases for both the positive and negative functionalities of the web-page.

## Features

- ### Support for All Open-Source LLM Models:
  - The application is built with comprehensive support for all major open-source and closed-source LLMs due to langchain's LLM abstraction layer. This allows users to select from a wide range of models, ensuring they can choose the one that best fits their specific needs and use cases.
- ### Adaptable for any web-site or web-page
  - The LLM prompts for page analaysis, page-specific test case and selenium script generation are extremely generic which enables the system's adaptablity with any web-site or web-page.
- ### URL extraction upto given depth parameter
  - Adjust the depth parameter in url_extract.py file to perform recursive unique url extraction upto that depth with Breadth-First-Search(BFS). The parameter can either be provided using CLI or directly in the function call itself.
- ### Dyanamic data-driven testing
  - The valid and invalid set of test data can be provided in the ``auth_test_data.json`` file for data-driven test case generation. The test case will include the test data only if there is a requirement for authentication or fill-out forms on the page to be tested.
- ### Context-aware test case generation
  - The page-metadata and HTML page-source are provided in the LLM prompt itself for ensuring page specific and context aware test case generation.
- ### Dual model support for page analysis and selenium code generation
  - Currently the system utilizes two different models for page analysis along with test case generation and selenium script generation.
  - Analysis model: "gpt-4o-2024-11-20"
  - Selenium model: "gpt-4.1-2025-04-14"
  - Follow the same format given in ``llm_config.yaml`` file to introduce and utilize different models as per the requirement:
  ```
  model_provider: "openai"  # Options: openai, groq, anthropic, etc.
  model_settings:
    openai:
      analysis_model: "gpt-4o-2024-11-20" # For page analysis and test generation
      selenium_model: "gpt-4.1-2025-04-14" # For script generation
      temperature: 0.2
  ```
- ### Robust web-page analysis technique using both static functions with common selenium selectors and LLM-powered analysis
  - The system performs robust and dynamic analysis of the target web-page to extract the page's metadata using a two-pronged approach.
  - In the first approach it leverages LLM-powered dynamic extraction of page metadata which are parsed in a valid specified JSON format.
  - Secondly it uses standard selenium selectors in static functions to extract the page metadata as a fallback if the LLM-powered dynamic metadata extraction fails.
- ### Provision in generated code to wait for web-page's Javascript/AJAX to finish loading before starting test steps
  - In some pages the javascript and AJAX loading may take time, so the generated test script will contain a waiting provision to handle slow JS/AJAX framework loading.
- ### Provision of manual intervention
  - If the web-page contains any security requirement like 'CAPTCHA', then the test process will wait for some time and allow the user to resolve the security requirement and then proceed the test. 



## Getting Started

Instructions on how to get started with your project, including installation, prerequisites, and basic usage.

### Prerequisites

- Understanding of test cases for web-pages
- Knowledge of Selenium test scripts
- Selenium version==4.15.2
- webdriver-manager version==4.0.2
- Make sure to have python version 3.10.12 installed
- Ensure to have the necessary provider's(like openai or gemini) API key in ``.env`` file required to access the LLM. For example ``OPENAI_API_KEY=place-your-api-key-here``

### Installation

To install the ``autotest`` tool:
  - Clone the repo
  - Navigate to your project folder
  - Create virtualenv using:
    - For Linux/Ubuntu-  ``python3 -m venv myenv``
    - For Windows, open Command Prompt or PowerShell, and run- ``python -m venv myenv``
    - For further reference, visit this [LINK](https://www.geeksforgeeks.org/creating-python-virtual-environment-windows-linux/)
  - Activate the virtual environment 
    - For Linux/Ubuntu using ``source myenv/bin/activate``
    - For Windows using ``myenv\Scripts\activate``
  - Navigate to the main folder ``cd selenium-based-llm-model``
  - Install requirements using requirements.txt ``pip install -r requirements.txt``
  - If using ``playwright`` testing framework, then also install the following dependency: ``playwright install chromium``
  - Provide the test data in ``auth_test_data.json`` file in the same directory.
  - Provide the name of the testing data file in the functional arguements of this given method:
  ```
  def load_test_data(self, file_path="auth_test_data.json"):
        try:
            with open(file_path) as f:
                data = json.load(f)
                
            #validate(data, AUTH_DATA_SCHEMA)
            return data
        except Exception as e:
            self.logger.error(f"Failed to load test data: {str(e)}")
            return None
  ```
  - Follow exactly same schema for test data as specified under [Usage](#usage) heading.
  - Run the autotest application using command ``python autotest.py --url "url-to-be-tested" --loglevel DEBUG``
  - Run the url extraction utility using the command ``python url_extract.py --url "base-url" --depth 1 --loglevel INFO``
  - Provide the LLM configuration in ``llm_config.yaml`` file.

To install and build the autotest python package:
  - Clone the repo
  - Navigate to your project folder
  - Create virtualenv using:
    - For Linux/Ubuntu-  ``python3 -m venv myenv``
    - For Windows, open Command Prompt or PowerShell, and run- ``python -m venv myenv``
    - For further reference, visit this [LINK](https://www.geeksforgeeks.org/creating-python-virtual-environment-windows-linux/)
  - Activate the virtual environment 
    - For Linux/Ubuntu using ``source myenv/bin/activate``
    - For Windows using ``myenv\Scripts\activate``
  - Navigate to the main folder ``cd autotest_package``
  - Install the package in Editable (Development) mode: ``pip install -e .``
  - Run the CLI to check if your package is available (Verify Installation): ``autotest-cli --help``
  - Or build a wheel for distribution:
    ``pip install build``
    ``python -m build``
  - This creates dist/ directory with:
    ``autotest_web_generator-1.0.0-py3-none-any.whl``
    ``autotest_web_generator-1.0.0.tar.gz``
  - Install the built package: ``pip install dist/autotest_web_generator-1.0.0-py3-none-any.whl``
  - Now get started by using the package via CLI: ``autotest-cli --url https://example.com --loglevel DEBUG --wait-time "30 seconds" --testing-tool "selenium" --language "python"``

## Usage

The application is mainly a CLI(Command-line-interface) based tool. The primary command line parameters include:
  - Base URL
  - Depth parameter (optional, default url extraction depth is set as 1)
  - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

- The logs for the entire testing process will be stored in the ``logs`` folder. Run the program in DEBUG logging level to check very detailed logs including the test cases parsed in JSON format.
- The generated selenium test scripts in the ``test_scripts`` folder. Create the folder in the same directory as the source code.
- The test results and reports are generated and stored in ``reports`` folder.
- In the ``.env`` file(in same directory as source code), place your API key: ``OPENAI_API_KEY=your-api-key``

If the user wants to perform a data-driven test for forms or login/registration pages, then the valid and invalid set of inputs must be provided in the ``auth_test_data.json`` in the following given schema.

### Test data schema

```
AUTH_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "credentials": {
            "type": "object",
            "properties": {
                "valid": {"type": "object"},
                "invalid": {"type": "object"}
            }
        },
        "registration_fields": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "properties": {
                        "valid": {"type": "array"},
                        "invalid": {"type": "array"}
                    }
                }
            }
        },
        "contact_form": {
            "type": "object",
            "properties": {
                "valid": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "message": {"type": "string"}
                    }
                },
                "invalid": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "message": {"type": "string"}
                    }
                }
            }
        }
    }
}
```

### Typical test case schema

```
{
  "name": "Submit login form with invalid credentials",
  "type": "auth-negative",
  "steps": [
    "Navigate to https://tt.ourgoalplan.co.in/Login/Login?returnUrl=%2f",
    "Enter invalid username in the username field",
    "Enter invalid password in the password field",
    "Click the submit button"
  ],
  "selectors": {
    "username_field": "#UserName",
    "password_field": "#Password",
    "submit_button": "input[type='submit']"
  },
  "validation": "Error message is displayed indicating invalid credentials",
  "test_data": {
    "username": "invaliduser",
    "password": "short"
  }
}
```

### Adaptable with any other testing framework
- Update or modify the user-prompt in ``generate_script_for_test_case`` function present in ``autotest.py`` to specify any different testing framework other than Selenium.
- The system is completely adaptable with any testing framework, but make sure to install the required packages associated with corresponding testing framework before executing the test scripts.

### Common errors
- If you encounter issue with recent versions of Chrome and the webdriver_manager package like:
 ```- ERROR - Test Case TC001 failed: [Errno 8] Exec format error: '/home/ankits/.wdm/drivers/chromedriver/linux64/131.0.6778.264/chromedriver-linux64/THIRD_PARTY_NOTICES.chromedriver'```

- The error occurs because the webdriver_manager is incorrectly selecting the THIRD_PARTY_NOTICES.chromedriver file instead of the actual chromedriver executable.
- The root cause of this error is that the webdriver_manager package (prior to version 4.0.2) incorrectly identifies this notices file as the actual chromedriver executable, resulting in the "Exec format error" when your script attempts to run it.

- There are several ways to fix this issue:
  - Update webdriver_manager to version 4.0.2 or later. The issue has been fixed in webdriver_manager version 4.0.2: ``pip install --upgrade webdriver-manager==4.0.2``
  - Clear the webdriver_manager cache. Even after updating, you may need to delete the cached drivers: ``rm -rf ~/.wdm/drivers``
  - Additionally, you should delete the drivers.json cache file: ``rm ~/.wdm/drivers.json``


## Contributing

Guidelines for contributing to the project. Provide information on how users can contribute, submit issues, or make pull requests.
Add link to [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Future Scope and improvements

- Continuous analysis and generation of test cases with selenium scripts for the following next pages after login/authentication requirement on the current page is satisfied and completed.
- The current version recursively extracts unique pages or urls from the base or given url, then analyzes and produces test cases and selenium scripts for execution in an automated manner.
- Analysing and giving suggestions on the improvement of the web-pages content.
- Checking whether web-page is upto the latest SEO standards.
- Moving or externalizing all the LLM prompts in a configuration file(.yaml) which allows easy modification and enhanced prompt engineering. (already achieved, checkout 'dev' branch)

## New features

- The latest code with the updated new features are on the ``dev`` branch.
- Externalisation of all LLM prompts to ``prompts3.yaml``.
- The updated source code of the tool is in ``selenium-based-llm-model/autotest_v2.py``
- Replace the ``prompt_file`` with your prompt filename in the ``PromptManager`` class of ``autotest_v2.py``
```class PromptManager:
    def __init__(self, prompt_file="prompts3.yaml"):
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompts = yaml.safe_load(f)
```
- Several optional CLI input parameters and prompt template customization has been introduced.
- ``--selenium-version``, ``wait-time``, ``testing-tool`` and ``--language``are the CLI parameters which can be provided by the user when starting the testing process.
- Format of input: ``python autotest_v2.py --url "url-to-be-tested" --loglevel DEBUG --selenium-version 4.15.2 --wait-time "30 seconds" --testing-tool "selenium" --language "Python"``
- Currently the following testing tool or frameworks are supported: ``selenium`` and ``playwright``
- Although multiple programming languages that are supported by respective testing frameworks are provided, the current version only generates testing script in ``Python`` programming language. Support for other valid languages are under development.
- Support for ``Puppeteer`` testing framework/tool has been integrated (dev->selenium-based-llm-model->autotest_v3.py)
- Customised prompt template added for ``puppeteer`` added in ``prompts4.yaml``
- To check it out, visit the ``dev`` branch and follow the same instructions as already stated in above sections. Run this command: ```python autotest_v3.py --url "www.example.com" --loglevel --wait-time "40 seconds" --testing-tool "puppeteer" --language "python" ``` 
- Before trying the ``pupeeteer`` make sure to satisfy the following requirements:
  - Install chromium browser dependency. For Ubuntu/Linux systems use- ``sudo apt-get install chromium`` or ``sudo snap install chromium``
  - Provide the exact same path of the chromium browser in the ``executablePath`` of the test scripts or provide the path in the LLM prompt template itself. Check the path using: ``which chromium`` command for Linux systems.
  - On executing the scripts, if you face errors like ``Browser closed unexpectedly`` then perform the following steps:
    - Create and set permissions for the temporary profile directory: 
      - ``mkdir -p /tmp/pyppeteer_profile``
      - ``chmod 700 /tmp/pyppeteer_profile``
    - Allow Chromium to access necessary system resources:
      - sudo snap connect chromium:removable-media
      - sudo snap connect chromium:system-observe
    -  Install Missing Codecs (Critical for Headless):
      - sudo apt-get install -y libva2 libva-drm2 libva-x11-2 vainfo
      - sudo apt-get install -y libnss3 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxi6 libxtst6 libxss1 libxrandr2 libasound2
    - Install Missing Dependencies
      - sudo apt-get install -y libgbm-dev libxshmfence-dev libdrm-dev
  - All the above mentioned steps for setting up and trouble-shooting issues due to chromium browser are for Linux/Ubuntu systems. For Windows or other systems refer to necessary [Docs](https://www.chromium.org/getting-involved/download-chromium/) for chromium browser installation process.

- Python package with compiled modules with a fully automated workflow, LLM-powered test generation and execution pipeline, accessible from the terminal.
- Features of autotest-web-generator package:
  - Code-base restructured and python package compiled with build.
  - Optimised and compressed extracted page source for reducing cost of LLM invocation by decomposing non-interactive mark-up element tags from page source.
  - Provision for manual intervention before generating any test script, allowing the user to generate test script for any specific test case, hence giving the user more control.
  - List of available test cases displayed with proper execution steps and validation message.
  - Test result report improved: test-case name and file-name mapped with their corresponding execution results.
  - Issues with test result reporting resolved: success/failure detection fixed in generated report.
  - Caching of LLM responses implemented for identical page structures.
  - "--no-cache" parameter introduced for explicit test-case/script re-generation.
  - SQLite database integrated for caching responses generated by LLM and for test script re-generation from saved test-cases and page meta-data.
  - Comfirmation message added before script regeneration along with provision for entering user's choice.

## License

This project is licensed under the MIT license - see [LICENSE.md](LICENSE.md) for details.

## Acknowledgments

Give credit to any resources or individuals whose work or support has been instrumental to your project.
[Mindfire Digital LLP](https://www.mindfiresolutions.com/)
