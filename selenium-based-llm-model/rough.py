import os
import json
import re
import subprocess
import tempfile
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException, 
                                      NoSuchElementException,
                                      StaleElementReferenceException)
import groq
import openai
import base64
from io import BytesIO
from PIL import Image
import argparse
import logging
from datetime import datetime
from jsonschema import validate, ValidationError
#from parse_llm_code import extract_first_code
#from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

SUPPORTED_LANGUAGES = {
    "selenium": ["python", "java", "csharp", "javascript", "ruby"],
    "playwright": ["python", "javascript", "csharp", "java"],
    "puppeteer": ["python"]
}

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

load_dotenv()

class ContextFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'test_cases'):
            record.test_cases = []
        return True
    
#from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import yaml

# Hardcoded test cases in JSON format
test_cases = [
     {
      "name": "Upload a file using the file input",
      "type": "functional",
      "steps": [
        "Navigate to https://demoqa.com/upload-download",
        "Select a file to upload using the file input field"
      ],
      "selectors": {
        "file_input": "input#uploadFile"
      },
      "validation": "File is selected and file name is displayed or upload is successful",
      "test_data": {}
    }
]

# Hardcoded page metadata in JSON format
page_metadata ={'title': 'DEMOQA', 'url': 'https://demoqa.com/upload-download', 'forms': [{'id': '', 'action': 'https://demoqa.com/upload-download', 'method': 'get', 'inputs': [{'type': 'file', 'name': '', 'id': 'uploadFile'}], 'buttons': []}], 'buttons': [{'tag': 'a', 'text': '', 'id': 'close-fixedban', 'type': ''}, {'tag': 'a', 'text': '', 'id': '', 'type': ''}, {'tag': 'button', 'text': '', 'id': '', 'type': 'button'}, {'tag': 'a', 'text': 'Download', 'id': 'downloadButton', 'type': ''}, {'tag': 'input', 'text': '', 'id': 'uploadFile', 'type': 'file'}, {'tag': 'a', 'text': '', 'id': '', 'type': ''}], 'tables': [], 'key_flows': {'main_navigation': [], 'primary_actions': []}, 'auth_requirements': {'auth_required': False, 'auth_type': 'none', 'auth_fields': [], 'credentials_hint': ''}, 'contact_form_fields': [{'id': '', 'action': '', 'method': 'get', 'fields': [{'name': 'uploadFile', 'type': 'file', 'required': False, 'selector': 'input#uploadFile', 'validation_indicators': []}], 'submit_button': None}], 'interactive_elements': [{'type': 'link', 'text': 'Logo image', 'selector': "header > a[href='https://demoqa.com']", 'action': 'click', 'expected_outcome': 'redirects to https://demoqa.com', 'sub_elements': []}, {'type': 'menu', 'text': 'Elements', 'selector': '.element-group:nth-child(1) .group-header', 'action': 'click', 'expected_outcome': 'expands menu', 'sub_elements': [{'type': 'button', 'text': 'Text Box', 'selector': '.element-group:nth-child(1) .menu-list #item-0', 'action': 'click', 'expected_outcome': 'redirects to Text Box page'}, {'type': 'button', 'text': 'Check Box', 'selector': '.element-group:nth-child(1) .menu-list #item-1', 'action': 'click', 'expected_outcome': 'redirects to Check Box page'}, {'type': 'button', 'text': 'Radio Button', 'selector': '.element-group:nth-child(1) .menu-list #item-2', 'action': 'click', 'expected_outcome': 'redirects to Radio Button page'}, {'type': 'button', 'text': 'Web Tables', 'selector': '.element-group:nth-child(1) .menu-list #item-3', 'action': 'click', 'expected_outcome': 'redirects to Web Tables page'}, {'type': 'button', 'text': 'Buttons', 'selector': '.element-group:nth-child(1) .menu-list #item-4', 'action': 'click', 'expected_outcome': 'redirects to Buttons page'}, {'type': 'button', 'text': 'Links', 'selector': '.element-group:nth-child(1) .menu-list #item-5', 'action': 'click', 'expected_outcome': 'redirects to Links page'}, {'type': 'button', 'text': 'Broken Links - Images', 'selector': '.element-group:nth-child(1) .menu-list #item-6', 'action': 'click', 'expected_outcome': 'redirects to Broken Links - Images page'}, {'type': 'button', 'text': 'Upload and Download', 'selector': '.element-group:nth-child(1) .menu-list #item-7', 'action': 'click', 'expected_outcome': 'redirects to Upload and Download page'}, {'type': 'button', 'text': 'Dynamic Properties', 'selector': '.element-group:nth-child(1) .menu-list #item-8', 'action': 'click', 'expected_outcome': 'redirects to Dynamic Properties page'}]}, {'type': 'menu', 'text': 'Forms', 'selector': '.element-group:nth-child(2) .group-header', 'action': 'click', 'expected_outcome': 'expands menu', 'sub_elements': [{'type': 'button', 'text': 'Practice Form', 'selector': '.element-group:nth-child(2) .menu-list #item-0', 'action': 'click', 'expected_outcome': 'redirects to Practice Form page'}]}, {'type': 'menu', 'text': 'Alerts, Frame & Windows', 'selector': '.element-group:nth-child(3) .group-header', 'action': 'click', 'expected_outcome': 'expands menu', 'sub_elements': [{'type': 'button', 'text': 'Browser Windows', 'selector': '.element-group:nth-child(3) .menu-list #item-0', 'action': 'click', 'expected_outcome': 'redirects to Browser Windows page'}, {'type': 'button', 'text': 'Alerts', 'selector': '.element-group:nth-child(3) .menu-list #item-1', 'action': 'click', 'expected_outcome': 'redirects to Alerts page'}, {'type': 'button', 'text': 'Frames', 'selector': '.element-group:nth-child(3) .menu-list #item-2', 'action': 'click', 'expected_outcome': 'redirects to Frames page'}, {'type': 'button', 'text': 'Nested Frames', 'selector': '.element-group:nth-child(3) .menu-list #item-3', 'action': 'click', 'expected_outcome': 'redirects to Nested Frames page'}, {'type': 'button', 'text': 'Modal Dialogs', 'selector': '.element-group:nth-child(3) .menu-list #item-4', 'action': 'click', 'expected_outcome': 'redirects to Modal Dialogs page'}]}, {'type': 'menu', 'text': 'Widgets', 'selector': '.element-group:nth-child(4) .group-header', 'action': 'click', 'expected_outcome': 'expands menu', 'sub_elements': [{'type': 'button', 'text': 'Accordian', 'selector': '.element-group:nth-child(4) .menu-list #item-0', 'action': 'click', 'expected_outcome': 'redirects to Accordian page'}, {'type': 'button', 'text': 'Auto Complete', 'selector': '.element-group:nth-child(4) .menu-list #item-1', 'action': 'click', 'expected_outcome': 'redirects to Auto Complete page'}, {'type': 'button', 'text': 'Date Picker', 'selector': '.element-group:nth-child(4) .menu-list #item-2', 'action': 'click', 'expected_outcome': 'redirects to Date Picker page'}, {'type': 'button', 'text': 'Slider', 'selector': '.element-group:nth-child(4) .menu-list #item-3', 'action': 'click', 'expected_outcome': 'redirects to Slider page'}, {'type': 'button', 'text': 'Progress Bar', 'selector': '.element-group:nth-child(4) .menu-list #item-4', 'action': 'click', 'expected_outcome': 'redirects to Progress Bar page'}, {'type': 'button', 'text': 'Tabs', 'selector': '.element-group:nth-child(4) .menu-list #item-5', 'action': 'click', 'expected_outcome': 'redirects to Tabs page'}, {'type': 'button', 'text': 'Tool Tips', 'selector': '.element-group:nth-child(4) .menu-list #item-6', 'action': 'click', 'expected_outcome': 'redirects to Tool Tips page'}, {'type': 'button', 'text': 'Menu', 'selector': '.element-group:nth-child(4) .menu-list #item-7', 'action': 'click', 'expected_outcome': 'redirects to Menu page'}, {'type': 'button', 'text': 'Select Menu', 'selector': '.element-group:nth-child(4) .menu-list #item-8', 'action': 'click', 'expected_outcome': 'redirects to Select Menu page'}]}, {'type': 'menu', 'text': 'Interactions', 'selector': '.element-group:nth-child(5) .group-header', 'action': 'click', 'expected_outcome': 'expands menu', 'sub_elements': [{'type': 'button', 'text': 'Sortable', 'selector': '.element-group:nth-child(5) .menu-list #item-0', 'action': 'click', 'expected_outcome': 'redirects to Sortable page'}, {'type': 'button', 'text': 'Selectable', 'selector': '.element-group:nth-child(5) .menu-list #item-1', 'action': 'click', 'expected_outcome': 'redirects to Selectable page'}, {'type': 'button', 'text': 'Resizable', 'selector': '.element-group:nth-child(5) .menu-list #item-2', 'action': 'click', 'expected_outcome': 'redirects to Resizable page'}, {'type': 'button', 'text': 'Droppable', 'selector': '.element-group:nth-child(5) .menu-list #item-3', 'action': 'click', 'expected_outcome': 'redirects to Droppable page'}, {'type': 'button', 'text': 'Dragabble', 'selector': '.element-group:nth-child(5) .menu-list #item-4', 'action': 'click', 'expected_outcome': 'redirects to Dragabble page'}]}, {'type': 'menu', 'text': 'Book Store Application', 'selector': '.element-group:nth-child(6) .group-header', 'action': 'click', 'expected_outcome': 'expands menu', 'sub_elements': [{'type': 'button', 'text': 'Login', 'selector': '.element-group:nth-child(6) .menu-list #item-0', 'action': 'click', 'expected_outcome': 'redirects to Login page'}, {'type': 'button', 'text': 'Book Store', 'selector': '.element-group:nth-child(6) .menu-list #item-2', 'action': 'click', 'expected_outcome': 'redirects to Book Store page'}, {'type': 'button', 'text': 'Profile', 'selector': '.element-group:nth-child(6) .menu-list #item-3', 'action': 'click', 'expected_outcome': 'redirects to Profile page'}, {'type': 'button', 'text': 'Book Store API', 'selector': '.element-group:nth-child(6) .menu-list #item-4', 'action': 'click', 'expected_outcome': 'redirects to Book Store API page'}]}, {'type': 'link', 'text': 'Download', 'selector': 'a#downloadButton', 'action': 'click', 'expected_outcome': 'downloads sampleFile.jpeg', 'sub_elements': []}, {'type': 'button', 'text': 'Navbar toggler', 'selector': '.navbar-toggler', 'action': 'click', 'expected_outcome': 'expands/collapses left menu', 'sub_elements': []}, {'type': 'link', 'text': 'Build PlayWright tests with AI', 'selector': '.Advertisement-Section .Google-Ad a', 'action': 'click', 'expected_outcome': 'unknown (ad link)', 'sub_elements': []}, {'type': 'button', 'text': 'Close fixed banner', 'selector': '#close-fixedban', 'action': 'click', 'expected_outcome': 'hides fixed banner', 'sub_elements': []}], 'ui_validation_indicators': [{'element_selector': 'input#uploadFile', 'validation_type': 'attribute', 'validation_value': 'type=file', 'description': 'File input field present for upload'}], 'main_content': "The main content area provides a heading 'Upload and Download', a download link for a sample file, and a file upload form. There are also advertisements and a sidebar.", 'key_actions': ['Download sample file', 'Upload a file', 'Navigate using left menu to other demo pages'], 'content_hierarchy': {'primary_sections': ['Header (logo)', 'Left navigation menu', 'Main content (Upload and Download)', 'Sidebar (ads)', 'Footer'], 'subsections': ['Download link', 'File upload form', 'Advertisements']}, 'security_indicators': ['https', 'file_upload']}

# Hardcoded page source as a string
page_source = """
<html><head><meta http-equiv="origin-trial" content="A7vZI3v+Gz7JfuRolKNM4Aff6zaGuT7X0mf3wtoZTnKv6497cVMnhy03KDqX7kBz/q/iidW7srW31oQbBt4VhgoAAACUeyJvcmlnaW4iOiJodHRwczovL3d3dy5nb29nbGUuY29tOjQ0MyIsImZlYXR1cmUiOiJEaXNhYmxlVGhpcmRQYXJ0eVN0b3JhZ2VQYXJ0aXRpb25pbmczIiwiZXhwaXJ5IjoxNzU3OTgwODAwLCJpc1N1YmRvbWFpbiI6dHJ1ZSwiaXNUaGlyZFBhcnR5Ijp0cnVlfQ=="><meta name="viewport" content="width=device-width,initial-scale=1"><script type="text/javascript" async="" src="https://www.google-analytics.com/analytics.js"></script><script type="text/javascript" async="" src="https://www.googletagmanager.com/gtag/js?id=G-MVRXK93D28&amp;cx=c&amp;gtm=45He56g0v855226469za200&amp;tag_exp=101509157~102015666~103116026~103200004~103233427~103351869~103351871~104684204~104684207~104718208~104791498~104791500"></script><script src="https://pagead2.googlesyndication.com/pagead/managed/js/adsense/m202506170101/show_ads_impl.js"></script><script type="text/javascript" async="" charset="utf-8" src="https://www.gstatic.com/recaptcha/releases/h7qt2xUGz2zqKEhSc8DD8baZ/recaptcha__en.js" crossorigin="anonymous" integrity="sha384-R2p1xdGKcSzm/oeFxRBmUuFAKdZRdY7u+SIsHBFbhXYxXlZ0TQJejBaVuyPwEVKn"></script><script async="" src="https://www.googletagmanager.com/gtm.js?id=GTM-MX8DD4S"></script><script src="https://code.jquery.com/jquery-3.5.0.min.js" integrity="sha256-xNzN2a4ltkB44Mc/Jz3pT4iU1cmeR0FkXs4pru/JxaQ=" crossorigin="anonymous"></script><script src="https://code.jquery.com/ui/1.12.0/jquery-ui.min.js" integrity="sha256-eGE6blurk5sHj+rmkfsGYeKyZx3M4bG+ZlFyA7Kns7E=" crossorigin="anonymous"></script><link href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous"><script async="">async function detectAdBlock(){let e=!1;try{await fetch(new Request("https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js")).catch(t=>e=!0)}catch(t){e=!1}finally{!0===e&&dataLayer.push({event:"Ad Blocker"}),console.log("AdBlock Enabled: "+e)}}detectAdBlock()</script><script async="" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5889298451609146" crossorigin="anonymous" data-checked-head="true"></script><title>DEMOQA</title><meta http-equiv="origin-trial" content="AlK2UR5SkAlj8jjdEc9p3F3xuFYlF6LYjAML3EOqw1g26eCwWPjdmecULvBH5MVPoqKYrOfPhYVL71xAXI1IBQoAAAB8eyJvcmlnaW4iOiJodHRwczovL2RvdWJsZWNsaWNrLm5ldDo0NDMiLCJmZWF0dXJlIjoiV2ViVmlld1hSZXF1ZXN0ZWRXaXRoRGVwcmVjYXRpb24iLCJleHBpcnkiOjE3NTgwNjcxOTksImlzU3ViZG9tYWluIjp0cnVlfQ=="><meta http-equiv="origin-trial" content="Amm8/NmvvQfhwCib6I7ZsmUxiSCfOxWxHayJwyU1r3gRIItzr7bNQid6O8ZYaE1GSQTa69WwhPC9flq/oYkRBwsAAACCeyJvcmlnaW4iOiJodHRwczovL2dvb2dsZXN5bmRpY2F0aW9uLmNvbTo0NDMiLCJmZWF0dXJlIjoiV2ViVmlld1hSZXF1ZXN0ZWRXaXRoRGVwcmVjYXRpb24iLCJleHBpcnkiOjE3NTgwNjcxOTksImlzU3ViZG9tYWluIjp0cnVlfQ=="><meta http-equiv="origin-trial" content="A9wSqI5i0iwGdf6L1CERNdmsTPgVu44ewj8QxTBYgsv1LCPUVF7YmWOvTappqB1139jAymxUW/RO8zmMqo4zlAAAAACNeyJvcmlnaW4iOiJodHRwczovL2RvdWJsZWNsaWNrLm5ldDo0NDMiLCJmZWF0dXJlIjoiRmxlZGdlQmlkZGluZ0FuZEF1Y3Rpb25TZXJ2ZXIiLCJleHBpcnkiOjE3MzY4MTI4MDAsImlzU3ViZG9tYWluIjp0cnVlLCJpc1RoaXJkUGFydHkiOnRydWV9"><meta http-equiv="origin-trial" content="A+d7vJfYtay4OUbdtRPZA3y7bKQLsxaMEPmxgfhBGqKXNrdkCQeJlUwqa6EBbSfjwFtJWTrWIioXeMW+y8bWAgQAAACTeyJvcmlnaW4iOiJodHRwczovL2dvb2dsZXN5bmRpY2F0aW9uLmNvbTo0NDMiLCJmZWF0dXJlIjoiRmxlZGdlQmlkZGluZ0FuZEF1Y3Rpb25TZXJ2ZXIiLCJleHBpcnkiOjE3MzY4MTI4MDAsImlzU3ViZG9tYWluIjp0cnVlLCJpc1RoaXJkUGFydHkiOnRydWV9"><script src="https://securepubads.g.doubleclick.net/pagead/managed/js/gpt/m202506170101/pubads_impl.js" async=""></script><link href="https://securepubads.g.doubleclick.net/pagead/managed/dict/m202506170101/gpt" rel="compression-dictionary"><meta http-equiv="origin-trial" content="AlK2UR5SkAlj8jjdEc9p3F3xuFYlF6LYjAML3EOqw1g26eCwWPjdmecULvBH5MVPoqKYrOfPhYVL71xAXI1IBQoAAAB8eyJvcmlnaW4iOiJodHRwczovL2RvdWJsZWNsaWNrLm5ldDo0NDMiLCJmZWF0dXJlIjoiV2ViVmlld1hSZXF1ZXN0ZWRXaXRoRGVwcmVjYXRpb24iLCJleHBpcnkiOjE3NTgwNjcxOTksImlzU3ViZG9tYWluIjp0cnVlfQ=="><meta http-equiv="origin-trial" content="Amm8/NmvvQfhwCib6I7ZsmUxiSCfOxWxHayJwyU1r3gRIItzr7bNQid6O8ZYaE1GSQTa69WwhPC9flq/oYkRBwsAAACCeyJvcmlnaW4iOiJodHRwczovL2dvb2dsZXN5bmRpY2F0aW9uLmNvbTo0NDMiLCJmZWF0dXJlIjoiV2ViVmlld1hSZXF1ZXN0ZWRXaXRoRGVwcmVjYXRpb24iLCJleHBpcnkiOjE3NTgwNjcxOTksImlzU3ViZG9tYWluIjp0cnVlfQ=="><meta http-equiv="origin-trial" content="A9wSqI5i0iwGdf6L1CERNdmsTPgVu44ewj8QxTBYgsv1LCPUVF7YmWOvTappqB1139jAymxUW/RO8zmMqo4zlAAAAACNeyJvcmlnaW4iOiJodHRwczovL2RvdWJsZWNsaWNrLm5ldDo0NDMiLCJmZWF0dXJlIjoiRmxlZGdlQmlkZGluZ0FuZEF1Y3Rpb25TZXJ2ZXIiLCJleHBpcnkiOjE3MzY4MTI4MDAsImlzU3ViZG9tYWluIjp0cnVlLCJpc1RoaXJkUGFydHkiOnRydWV9"><meta http-equiv="origin-trial" content="A+d7vJfYtay4OUbdtRPZA3y7bKQLsxaMEPmxgfhBGqKXNrdkCQeJlUwqa6EBbSfjwFtJWTrWIioXeMW+y8bWAgQAAACTeyJvcmlnaW4iOiJodHRwczovL2dvb2dsZXN5bmRpY2F0aW9uLmNvbTo0NDMiLCJmZWF0dXJlIjoiRmxlZGdlQmlkZGluZ0FuZEF1Y3Rpb25TZXJ2ZXIiLCJleHBpcnkiOjE3MzY4MTI4MDAsImlzU3ViZG9tYWluIjp0cnVlLCJpc1RoaXJkUGFydHkiOnRydWV9"><script esp-signal="true" src="https://cdn-ima.33across.com/ob.js"></script><script esp-signal="true" src="https://cdn.id5-sync.com/api/1.0/esp.js"></script><script esp-signal="true" src="https://cdn.jsdelivr.net/gh/prebid/shared-id/pubcid.js/docs/pubcid.min.js"></script><script esp-signal="true" src="https://cdn.prod.uidapi.com/uid2SecureSignal.js"></script><script esp-signal="true" src="https://invstatic101.creativecdn.com/encrypted-signals/encrypted-tag-g.js"></script><script esp-signal="true" src="https://cdn.prod.euid.eu/euidSecureSignal.js"></script><script esp-signal="true" src="https://static.criteo.net/js/ld/publishertag.ids.js"></script><script esp-signal="true" src="https://oa.openxcdn.net/esp.js"></script><script esp-signal="true" src="https://tags.crwdcntrl.net/lt/c/16589/sync.min.js"></script><script src="https://cdn.ad.plus/player/adplus.js"></script></head><body><div id="fixedban" style="width:100%;margin:auto;text-align:center;float:none;overflow:hidden;display:scroll;position:fixed;bottom:0;z-index:9999999"><div style="text-align:center;display:block;max-width:970px;height:auto;overflow:hidden;margin:auto"><script async="async" src="https://www.googletagservices.com/tag/js/gpt.js"></script><script>var gptadslots=[],googletag=googletag||{cmd:[]}</script><script>googletag.cmd.push((function(){var e=googletag.sizeMapping().addSize([0,0],[[320,50],[300,75],[300,50]]).addSize([730,200],[[728,90],[468,60]]).addSize([975,200],[[970,90],[728,90],[960,90],[750,100],[950,90],[468,60]]).build();gptadslots.push(googletag.defineSlot("/21849154601,22343295815/Ad.Plus-Anchor",[[320,100]],"adplus-anchor").setTargeting("site",["demoqa.com"]).defineSizeMapping(e).addService(googletag.pubads())),googletag.enableServices()}))</script><div><a id="close-fixedban" onclick="document.getElementById(&quot;fixedban&amp;apos&quot;).style.display=&quot;none&amp;apos&quot;" style="cursor:pointer"><img src="https://ad.plus/adplus-advertising.svg" alt="adplus-dvertising" title="Ad.Plus Advertising" style="vertical-align:middle"></a></div><div id="adplus-anchor" data-google-query-id="CKvx-cW4h44DFWpnnQkdfIcrfQ"><div id="google_ads_iframe_/21849154601,22343295815/Ad.Plus-Anchor_0__container__" style="border: 0pt none; display: inline-block; width: 728px; height: 90px;"><iframe frameborder="0" src="https://8566210ab026158b2dd2592bc4ffd4b6.safeframe.googlesyndication.com/safeframe/1-0-45/html/container.html" id="google_ads_iframe_/21849154601,22343295815/Ad.Plus-Anchor_0" title="3rd party ad content" name="" scrolling="no" marginwidth="0" marginheight="0" width="728" height="90" data-is-safeframe="true" sandbox="allow-forms allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts allow-top-navigation-by-user-activation" allow="private-state-token-redemption;attribution-reporting" aria-label="Advertisement" tabindex="0" data-google-container-id="1" style="border: 0px; vertical-align: bottom;" data-load-complete="true"></iframe></div></div></div></div><script>!function(e,t,a,n,g){e[n]=e[n]||[],e[n].push({"gtm.start":(new Date).getTime(),event:"gtm.js"});var m=t.getElementsByTagName(a)[0],r=t.createElement(a);r.async=!0,r.src="https://www.googletagmanager.com/gtm.js?id=GTM-MX8DD4S",m.parentNode.insertBefore(r,m)}(window,document,"script","dataLayer")</script><link rel="shortcut icon" href="/favicon.png"><link href="/main.css" rel="stylesheet"><noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-MX8DD4S" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript><div id="app"><header><a href="https://demoqa.com"><img src="/images/Toolsqa.jpg"></a></header><div class="body-height"><div class="container playgound-body"><div class="row"><div class="col-12 mt-4  col-md-3"><nav class="navbar navbar-dark bg-dark left-menu-nav-bar"><button class="navbar-toggler" type="button"><span class="navbar-toggler-icon"></span></button></nav><div class="left-pannel"><div class="accordion"><div class="element-group"><span class="group-header"><div class="header-wrapper" style="background: rgb(108, 117, 125);"><div class="header-text"><span class="pr-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 448 512" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M16 132h416c8.837 0 16-7.163 16-16V76c0-8.837-7.163-16-16-16H16C7.163 60 0 67.163 0 76v40c0 8.837 7.163 16 16 16zm0 160h416c8.837 0 16-7.163 16-16v-40c0-8.837-7.163-16-16-16H16c-8.837 0-16 7.163-16 16v40c0 8.837 7.163 16 16 16zm0 160h416c8.837 0 16-7.163 16-16v-40c0-8.837-7.163-16-16-16H16c-8.837 0-16 7.163-16 16v40c0 8.837 7.163 16 16 16z"></path></svg></span>Elements</div><div class="header-right"><div class="separator">&nbsp;</div><div class="icon"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><g><path fill="none" d="M0 0h24v24H0z"></path><path d="M3 19h18v2H3v-2zM13 5.828V17h-2V5.828L4.929 11.9l-1.414-1.414L12 2l8.485 8.485-1.414 1.414L13 5.83z"></path></g></svg></div></div></div></span><div class="element-list collapse show"><ul class="menu-list"><li class="btn btn-light " id="item-0"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Text Box</span></li><li class="btn btn-light " id="item-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Check Box</span></li><li class="btn btn-light " id="item-2"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Radio Button</span></li><li class="btn btn-light " id="item-3"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Web Tables</span></li><li class="btn btn-light " id="item-4"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Buttons</span></li><li class="btn btn-light " id="item-5"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Links</span></li><li class="btn btn-light " id="item-6"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Broken Links - Images</span></li><li class="btn btn-light active" id="item-7"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Upload and Download</span></li><li class="btn btn-light " id="item-8"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Dynamic Properties</span></li></ul></div></div><div class="element-group"><span class="group-header"><div class="header-wrapper" style="background: rgb(108, 117, 125);"><div class="header-text"><span class="pr-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" version="1.2" baseProfile="tiny" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><g><path d="M17 21h-10c-1.654 0-3-1.346-3-3v-12c0-1.654 1.346-3 3-3h10c1.654 0 3 1.346 3 3v12c0 1.654-1.346 3-3 3zm-10-16c-.551 0-1 .449-1 1v12c0 .551.449 1 1 1h10c.551 0 1-.449 1-1v-12c0-.551-.449-1-1-1h-10zM16 11h-8c-.276 0-.5-.224-.5-.5s.224-.5.5-.5h8c.276 0 .5.224.5.5s-.224.5-.5.5zM16 8h-8c-.276 0-.5-.224-.5-.5s.224-.5.5-.5h8c.276 0 .5.224.5.5s-.224.5-.5.5zM16 14h-8c-.276 0-.5-.224-.5-.5s.224-.5.5-.5h8c.276 0 .5.224.5.5s-.224.5-.5.5zM16 17h-8c-.276 0-.5-.224-.5-.5s.224-.5.5-.5h8c.276 0 .5.224.5.5s-.224.5-.5.5z"></path></g></svg></span>Forms</div><div class="header-right"><div class="separator">&nbsp;</div><div class="icon"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><g><path fill="none" d="M0 0h24v24H0z"></path><path d="M3 19h18v2H3v-2zm10-5.828L19.071 7.1l1.414 1.414L12 17 3.515 8.515 4.929 7.1 11 13.17V2h2v11.172z"></path></g></svg></div></div></div></span><div class="element-list collapse"><ul class="menu-list"><li class="btn btn-light " id="item-0"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Practice Form</span></li></ul></div></div><div class="element-group"><span class="group-header"><div class="header-wrapper" style="background: rgb(108, 117, 125);"><div class="header-text"><span class="pr-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 14 16" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M5 3h1v1H5V3zM3 3h1v1H3V3zM1 3h1v1H1V3zm12 10H1V5h12v8zm0-9H7V3h6v1zm1-1c0-.55-.45-1-1-1H1c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1V3z"></path></svg></span>Alerts, Frame &amp; Windows</div><div class="header-right"><div class="separator">&nbsp;</div><div class="icon"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><g><path fill="none" d="M0 0h24v24H0z"></path><path d="M3 19h18v2H3v-2zm10-5.828L19.071 7.1l1.414 1.414L12 17 3.515 8.515 4.929 7.1 11 13.17V2h2v11.172z"></path></g></svg></div></div></div></span><div class="element-list collapse"><ul class="menu-list"><li class="btn btn-light " id="item-0"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Browser Windows</span></li><li class="btn btn-light " id="item-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Alerts</span></li><li class="btn btn-light " id="item-2"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Frames</span></li><li class="btn btn-light " id="item-3"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Nested Frames</span></li><li class="btn btn-light " id="item-4"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Modal Dialogs</span></li></ul></div></div><div class="element-group"><span class="group-header"><div class="header-wrapper" style="background: rgb(108, 117, 125);"><div class="header-text"><span class="pr-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M13 13v8h8v-8h-8zM3 21h8v-8H3v8zM3 3v8h8V3H3zm13.66-1.31L11 7.34 16.66 13l5.66-5.66-5.66-5.65z"></path></svg></span>Widgets</div><div class="header-right"><div class="separator">&nbsp;</div><div class="icon"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><g><path fill="none" d="M0 0h24v24H0z"></path><path d="M3 19h18v2H3v-2zm10-5.828L19.071 7.1l1.414 1.414L12 17 3.515 8.515 4.929 7.1 11 13.17V2h2v11.172z"></path></g></svg></div></div></div></span><div class="element-list collapse"><ul class="menu-list"><li class="btn btn-light " id="item-0"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Accordian</span></li><li class="btn btn-light " id="item-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Auto Complete</span></li><li class="btn btn-light " id="item-2"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Date Picker</span></li><li class="btn btn-light " id="item-3"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Slider</span></li><li class="btn btn-light " id="item-4"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Progress Bar</span></li><li class="btn btn-light " id="item-5"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Tabs</span></li><li class="btn btn-light " id="item-6"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Tool Tips</span></li><li class="btn btn-light " id="item-7"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Menu</span></li><li class="btn btn-light " id="item-8"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Select Menu</span></li></ul></div></div><div class="element-group"><span class="group-header"><div class="header-wrapper" style="background: rgb(108, 117, 125);"><div class="header-text"><span class="pr-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M880 112H144c-17.7 0-32 14.3-32 32v736c0 17.7 14.3 32 32 32h736c17.7 0 32-14.3 32-32V144c0-17.7-14.3-32-32-32zM726 585.7c0 55.3-44.7 100.1-99.7 100.1H420.6v53.4c0 5.7-6.5 8.8-10.9 5.3l-109.1-85.7c-3.5-2.7-3.5-8 0-10.7l109.1-85.7c4.4-3.5 10.9-.3 10.9 5.3v53.4h205.7c19.6 0 35.5-16 35.5-35.6v-78.9c0-3.7 3-6.8 6.8-6.8h50.7c3.7 0 6.8 3 6.8 6.8v79.1zm-2.6-209.9l-109.1 85.7c-4.4 3.5-10.9.3-10.9-5.3v-53.4H397.7c-19.6 0-35.5 16-35.5 35.6v78.9c0 3.7-3 6.8-6.8 6.8h-50.7c-3.7 0-6.8-3-6.8-6.8v-78.9c0-55.3 44.7-100.1 99.7-100.1h205.7v-53.4c0-5.7 6.5-8.8 10.9-5.3l109.1 85.7c3.6 2.5 3.6 7.8.1 10.5z"></path></svg></span>Interactions</div><div class="header-right"><div class="separator">&nbsp;</div><div class="icon"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><g><path fill="none" d="M0 0h24v24H0z"></path><path d="M3 19h18v2H3v-2zm10-5.828L19.071 7.1l1.414 1.414L12 17 3.515 8.515 4.929 7.1 11 13.17V2h2v11.172z"></path></g></svg></div></div></div></span><div class="element-list collapse"><ul class="menu-list"><li class="btn btn-light " id="item-0"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Sortable</span></li><li class="btn btn-light " id="item-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Selectable</span></li><li class="btn btn-light " id="item-2"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Resizable</span></li><li class="btn btn-light " id="item-3"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Droppable</span></li><li class="btn btn-light " id="item-4"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Dragabble</span></li></ul></div></div><div class="element-group"><span class="group-header"><div class="header-wrapper" style="background: rgb(108, 117, 125);"><div class="header-text"><span class="pr-1"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 512 512" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M169 57v430h78V57h-78zM25 105v190h46V105H25zm158 23h18v320h-18V128zm128.725 7.69l-45.276 8.124 61.825 344.497 45.276-8.124-61.825-344.497zM89 153v270h62V153H89zm281.502 28.68l-27.594 11.773 5.494 12.877 27.594-11.773-5.494-12.877zm12.56 29.433l-27.597 11.772 5.494 12.877 27.593-11.772-5.492-12.877zm12.555 29.434l-27.594 11.77 99.674 233.628 27.594-11.773-99.673-233.625zM25 313v30h46v-30H25zm190 7h18v128h-18V320zM25 361v126h46V361H25zm64 80v46h62v-46H89z"></path></svg></span>Book Store Application</div><div class="header-right"><div class="separator">&nbsp;</div><div class="icon"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 24 24" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><g><path fill="none" d="M0 0h24v24H0z"></path><path d="M3 19h18v2H3v-2zm10-5.828L19.071 7.1l1.414 1.414L12 17 3.515 8.515 4.929 7.1 11 13.17V2h2v11.172z"></path></g></svg></div></div></div></span><div class="element-list collapse"><ul class="menu-list"><li class="btn btn-light " id="item-0"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Login</span></li><li class="btn btn-light " id="item-2"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Book Store</span></li><li class="btn btn-light " id="item-3"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Profile</span></li><li class="btn btn-light " id="item-4"><svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M145.2 96l66 746.6L512 928l299.6-85.4L878.9 96H145.2zm595 177.1l-4.8 47.2-1.7 19.5H382.3l8.2 94.2h335.1l-3.3 24.3-21.2 242.2-1.7 16.2-187 51.6v.3h-1.2l-.3.1v-.1h-.1l-188.6-52L310.8 572h91.1l6.5 73.2 102.4 27.7h.4l102-27.6 11.4-118.6H510.9v-.1H306l-22.8-253.5-1.7-24.3h460.3l-1.6 24.3z"></path></svg><span class="text">Book Store API</span></li></ul></div></div></div></div></div><div class="col-12 mt-4 col-md-6"><div id="Ad.Plus-970x250-1" data-google-query-id="CIajoca4h44DFclynQkd2xovrw" style="margin-bottom: 50px;"><div id="google_ads_iframe_/21849154601,22343295815/Ad.Plus-970x250-1_0__container__" style="border: 0pt none; width: 970px; height: 0px;"></div></div><div><h1 class="text-center">Upload and Download</h1><div><a href="data:image/jpeg;base64,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" target="_blank" id="downloadButton" download="sampleFile.jpeg" class="btn btn-primary">Download</a></div><div class="mt-3"><form class=""><div class="form-file"><label for="uploadFile" class="form-file-label">Select a file</label><input id="uploadFile" type="file" lang="en" class="form-control-file"></div></form></div></div><div style="border: 1px solid rgb(229, 229, 229); margin-top: 50px; padding: 50px;"><div id="Ad.Plus-970x250-2" data-google-query-id="CKf0oMa4h44DFWB0nQkdhlAQ2w" style="margin-bottom: 50px;"><div id="google_ads_iframe_/21849154601,22343295815/Ad.Plus-970x250-2_0__container__" style="border: 0pt none; display: inline-block; width: 970px; height: 250px;"><iframe frameborder="0" src="https://8566210ab026158b2dd2592bc4ffd4b6.safeframe.googlesyndication.com/safeframe/1-0-45/html/container.html" id="google_ads_iframe_/21849154601,22343295815/Ad.Plus-970x250-2_0" title="3rd party ad content" name="" scrolling="no" marginwidth="0" marginheight="0" width="970" height="250" data-is-safeframe="true" sandbox="allow-forms allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts allow-top-navigation-by-user-activation" allow="private-state-token-redemption;attribution-reporting" aria-label="Advertisement" tabindex="0" data-google-container-id="3" style="border: 0px; vertical-align: bottom;" data-load-complete="true"></iframe></div></div></div><div></div></div><div class="col-12 mt-4 col-md-3"><div class="sidebar-content pattern-backgound shadow widget-divider-off"><section id="RightSide_Advertisement" class="widget widget_text"><div class="Advertisement-Section"><div class="Google-Ad"><a class="cursor-pointer" style="display: block;"><img src="/images/zero-step.jpeg" alt="Build PlayWright tests with AI" style="width: 300px;"></a><div id="Ad.Plus-300x250-1" data-google-query-id="CN_boMa4h44DFbBJnQkdrQg7Yg" style="margin-bottom: 50px;"><div id="google_ads_iframe_/21849154601,22343295815/Ad.Plus-300x250-1_0__container__" style="border: 0pt none; width: 300px; height: 0px;"></div></div><div id="Ad.Plus-300x250-2" data-google-query-id="CMjzoMa4h44DFS50nQkdDTctJA" style="margin-bottom: 50px;"><div id="google_ads_iframe_/21849154601,22343295815/Ad.Plus-300x250-2_0__container__" style="border: 0pt none; display: inline-block; width: 300px; height: 250px;"><iframe frameborder="0" src="https://8566210ab026158b2dd2592bc4ffd4b6.safeframe.googlesyndication.com/safeframe/1-0-45/html/container.html" id="google_ads_iframe_/21849154601,22343295815/Ad.Plus-300x250-2_0" title="3rd party ad content" name="" scrolling="no" marginwidth="0" marginheight="0" width="300" height="250" data-is-safeframe="true" sandbox="allow-forms allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts allow-top-navigation-by-user-activation" allow="private-state-token-redemption;attribution-reporting" aria-label="Advertisement" tabindex="0" data-google-container-id="5" style="border: 0px; vertical-align: bottom;" data-load-complete="true"></iframe></div></div></div></div></section></div></div></div></div></div><footer><span>© 2013-2020 TOOLSQA.COM | ALL RIGHTS RESERVED.</span></footer></div><script src="https://www.google.com/recaptcha/api.js?onload=onloadCallback&amp;render=explicit" async="" defer="defer"></script><script src="/bundle.js"></script><ins class="adsbygoogle adsbygoogle-noablate" data-adsbygoogle-status="done" style="display: none !important;" data-ad-status="unfilled"><div id="aswift_0_host" style="border: none; height: 0px; width: 0px; margin: 0px; padding: 0px; position: relative; visibility: visible; background-color: transparent; display: inline-block;"><iframe id="aswift_0" name="aswift_0" browsingtopics="true" style="left:0;position:absolute;top:0;border:0;width:undefinedpx;height:undefinedpx;min-height:auto;max-height:none;min-width:auto;max-width:none;" sandbox="allow-forms allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts allow-top-navigation-by-user-activation" frameborder="0" marginwidth="0" marginheight="0" vspace="0" hspace="0" allowtransparency="true" scrolling="no" allow="attribution-reporting; run-ad-auction" src="https://googleads.g.doubleclick.net/pagead/ads?client=ca-pub-5889298451609146&amp;output=html&amp;adk=1812271804&amp;adf=3025194257&amp;abgtt=6&amp;lmt=1710656768&amp;plat=9%3A32776%2C16%3A8388608%2C17%3A32%2C24%3A32%2C25%3A32%2C30%3A1081344%2C32%3A32%2C41%3A32%2C42%3A32&amp;plas=596x848_l%7C596x848_r&amp;format=0x0&amp;url=https%3A%2F%2Fdemoqa.com%2Fupload-download&amp;pra=5&amp;wgl=1&amp;aihb=0&amp;aiudt=1&amp;asro=0&amp;aifxl=29_18~30_19&amp;aiapm=0.1542&amp;aiapmd=0.15&amp;aiapmi=0.16&amp;aiapmid=0.16&amp;aiact=0.5423&amp;aiactd=0.7&amp;aicct=0.6036331124524906&amp;aicctd=0.7&amp;ailct=0.7&amp;ailctd=0.7&amp;aimart=4&amp;aimartd=8&amp;uach=WyJMaW51eCIsIjYuOC4wIiwieDg2IiwiIiwiMTM3LjAuNzE1MS4xMTkiLG51bGwsMCxudWxsLCI2NCIsW1siR29vZ2xlIENocm9tZSIsIjEzNy4wLjcxNTEuMTE5Il0sWyJDaHJvbWl1bSIsIjEzNy4wLjcxNTEuMTE5Il0sWyJOb3QvQSlCcmFuZCIsIjI0LjAuMC4wIl1dLDBd&amp;dt=1750678208283&amp;bpp=11&amp;bdt=668&amp;idt=325&amp;shv=r20250617&amp;mjsv=m202506170101&amp;ptt=9&amp;saldr=aa&amp;abxe=1&amp;cookie_enabled=1&amp;eoidce=1&amp;nras=1&amp;correlator=92562785634&amp;frm=20&amp;pv=2&amp;u_tz=330&amp;u_his=2&amp;u_h=600&amp;u_w=800&amp;u_ah=600&amp;u_aw=800&amp;u_cd=24&amp;u_sd=1&amp;dmc=8&amp;adx=-12245933&amp;ady=-12245933&amp;biw=1920&amp;bih=941&amp;scr_x=0&amp;scr_y=0&amp;eid=95353386%2C95362436%2C95362655%2C95364339%2C95364386%2C95359265%2C95364337%2C95364390&amp;oid=2&amp;pvsid=4261890629498963&amp;tmod=486198651&amp;uas=0&amp;nvt=1&amp;fsapi=1&amp;fc=1920&amp;brdim=10%2C10%2C10%2C10%2C800%2C0%2C1920%2C1080%2C1920%2C941&amp;vis=1&amp;rsz=%7C%7Cs%7C&amp;abl=NS&amp;fu=32768&amp;bc=31&amp;bz=1&amp;td=1&amp;tdf=2&amp;psd=W251bGwsbnVsbCxudWxsLDNd&amp;nt=1&amp;ifi=1&amp;uci=a!1&amp;fsb=1&amp;dtd=342" data-google-container-id="a!1" tabindex="0" title="Advertisement" aria-label="Advertisement" data-load-complete="true"></iframe></div></ins><iframe src="https://gumi.criteo.com/syncframe?origin=publishertagids&amp;topUrl=demoqa.com#{&quot;bundle&quot;:{&quot;origin&quot;:0},&quot;optout&quot;:{&quot;value&quot;:false,&quot;origin&quot;:0},&quot;tld&quot;:&quot;demoqa.com&quot;,&quot;topUrl&quot;:&quot;demoqa.com&quot;,&quot;version&quot;:161,&quot;origin&quot;:&quot;publishertagids&quot;,&quot;requestId&quot;:&quot;0.6312042846953183&quot;}" width="0" height="0" frameborder="0" sandbox="allow-scripts allow-same-origin" aria-hidden="true" title="Criteo GUM iframe" style="border-width: 0px; margin: 0px; display: none;"></iframe><div><iframe src="https://google-bidout-d.openx.net/w/1.0/pd?plm=5" width="0" height="0" style="display:none;"></iframe></div></body><iframe name="goog_topics_frame" src="https://securepubads.g.doubleclick.net/static/topics/topics_frame.html" style="display: none;"></iframe><iframe id="google_esf" name="google_esf" src="https://googleads.g.doubleclick.net/pagead/html/r20250617/r20190131/zrt_lookup.html" style="display: none;"></iframe></html>
"""

class LLMWrapper:
    def __init__(self, config_path="llm_config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
            
        self.provider = self.config["model_provider"]
        #self.model = self._initialize_model()
        self.models = self._initialize_models()

    def _initialize_models(self):
        provider = self.config["model_provider"]
        params = self.config["model_settings"].get(provider, {})

        # Get API key based on provider
        api_key = os.getenv(
            "OPENAI_API_KEY" if provider == "openai" else "GROQ_API_KEY"
        )

        # Correct
        # ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model=..., temperature=...)
        if provider == "openai":
            #return ChatOpenAI(**params)
            return {
            "analysis": ChatOpenAI(api_key=api_key, model=params["analysis_model"], temperature=params["temperature"], model_kwargs={"response_format": {"type": "json_object"}}),
            "selenium": ChatOpenAI(api_key=api_key, model=params["selenium_model"], temperature=params["temperature"])
        }
        elif provider == "groq":
            return {
            "analysis": ChatGroq(api_key=api_key, model=params["analysis_model"], temperature=params["temperature"], model_kwargs={"response_format": {"type": "json_object"}}),
            "selenium": ChatGroq(api_key=api_key, model=params["selenium_model"], temperature=params["temperature"])
        }
        #     return ChatGroq(**params)
        elif provider == "google-gemini":
            return {
                "analysis": ChatGoogleGenerativeAI(api_key=os.getenv("GOOGLE_API_KEY"), model=params["analysis_model"], temperature=params["temperature"], model_kwargs={"response_format": {"type": "json_object"}}),
                "selenium": ChatGoogleGenerativeAI(api_key=os.getenv("GOOGLE_API_KEY"), model=params["selenium_model"], temperature=params["temperature"])
            }
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(self, system_prompt, user_prompt, model_type="analysis"):
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        #return self.model.invoke(messages).content
        return self.models[model_type].invoke(messages).content

class PromptManager:
    def __init__(self, prompt_file="prompts4.yaml"):
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompts = yaml.safe_load(f)

    def get_prompt(self, section, role, tool=None):
        """
        section: e.g., 'llm_page_analysis'
        role: 'system' or 'user'
        """
        #return self.prompts[section][role]
        if tool and section == "generate_script":
            return self.prompts[section][tool][role]
        return self.prompts[section][role]

class WebTestGenerator:
    def __init__(self, log_level="INFO", selenium_version="4.15.2", wait_time="", testing_tool="selenium", language="python"):
        self.log_level = log_level.upper()
        self.selenium_version = selenium_version
        self.wait_time = wait_time
        self.testing_tool = testing_tool.lower()

        # Validate language support
        valid_langs = SUPPORTED_LANGUAGES.get(testing_tool.lower(), [])
        if language.lower() not in valid_langs:
            raise ValueError(
                f"'{language}' not supported for {testing_tool}. "
                f"Valid options: {', '.join(valid_langs)}"
            )
        
        self.language = language.lower()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.llm = LLMWrapper()
        self.prompt_manager = PromptManager()
        #self.model = "llama-3.3-70b-versatile"
        #self.model = "gpt-4o-2024-08-06"
        #self.selenium_model = "meta-llama/llama-4-maverick-17b-128e-instruct"
        #self.selenium_model = "gpt-4.1-2025-04-14"
        #self.client = groq.Client(api_key=self.groq_api_key)
        #self.client = openai.OpenAI(api_key=self.openai_api_key)
        self.driver = None
        self.visited_pages = set()
        self.test_results = []
        self.logger = self.setup_logging()
        self.temperature = 0.3
        self.setup_browser()
        self.logger.addFilter(ContextFilter())
        self.logger.propagate = False  # Prevent duplicate logs
        self.url_extractor = URLExtractor(self.driver, self.logger)

    def setup_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)


    def setup_logging(self):
        # Convert string log level to numeric value
        numeric_level = getattr(logging, self.log_level, logging.INFO)
        
        logger = logging.getLogger("WebTestGenerator")
        logger.setLevel(numeric_level)
        
        # Remove existing handlers to prevent duplicates
        if logger.hasHandlers():
            logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        
        # Create file handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs('logs', exist_ok=True)
        log_file = f"logs/test_run_{timestamp}.log"
        
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger


    def capture_screenshot(self):
        screenshot = self.driver.get_screenshot_as_png()
        img = Image.open(BytesIO(screenshot))
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def analyze_page(self, context="current"):
        self.logger.info(f"Analyzing {context} page...")
        page_source = self.driver.page_source
        self.logger.info(f"PAGE_SOURCE: {page_source}")
        #page_source = self.driver.page_source[:5000]  # First 5000 characters for LLM context so that it doesn't exceed token limit
        
        # Static metadata extraction
        # page_metadata = {
        #     "title": self.driver.title,
        #     "url": self.driver.current_url,
        #     "forms": self.extract_forms(),
        #     "buttons": self.extract_interactive_elements(),
        #     "tables": self.extract_data_tables(),
        #     "key_flows": self.identify_key_flows()
        # }
        static_metadata = {
            "title": self.driver.title,
            "url": self.driver.current_url,
            "forms": self.extract_forms(),
            "buttons": self.extract_interactive_elements(),
            "tables": self.extract_data_tables(),
            "key_flows": self.identify_key_flows()
        }
        self.logger.debug(f"Static page metadata: {static_metadata}")
        
        # LLM-powered dynamic analysis
        llm_metadata = self.llm_page_analysis(page_source)
        self.logger.debug(f"LLM Analysed page metadata: {llm_metadata}")

        # Combine static and dynamic metadata
        page_metadata = {**static_metadata, **llm_metadata}
        self.logger.debug(f"Combined page metadata: {page_metadata}")

        test_cases = self.generate_page_specific_tests(page_metadata, page_source)
        scripts = [self.generate_script_for_test_case(tc, page_metadata, page_source) for tc in test_cases]
        
        return {
            "metadata": page_metadata,
            "test_cases": test_cases,
            "scripts": scripts
        }
    
    def llm_page_analysis(self, page_source):
        """Perform dynamic page analysis using LLM"""
        try:
            prompt = f"""Analyze this web page structure and return JSON metadata:
            {{
                "auth_requirements": {{
                    "auth_required": boolean,
                    "auth_type": "login|registration|none",
                    "auth_fields": [
                        {{
                            "name": "username",
                            "type": "email|text|password",
                            "required": boolean
                        }}
                    ]
                }},
                "contact_form_fields": [
                    {{
                        "name": "first name",
                        "type": "text",
                        "required": true
                    }},
                    {{
                        "name": "last name",
                        "type": "text",
                        "required": true
                    }},
                    {{
                        "name": "message",
                        "type": "text",
                        "required": true
                    }},
                    {{
                        "name": "email",
                        "type": "email",
                        "required": true
                    }}
                ],    
                "main_content": "Brief description of main content areas",
                "key_actions": ["list of primary user actions"],
                "content_hierarchy": {{
                    "primary_sections": ["section1", "section2"],
                    "subsections": ["subsection1", "subsection2"]
                }},
                "interactive_patterns": {{
                    "forms": ["login", "search"],
                    "dynamic_elements": ["live_search", "infinite_scroll"]
                }},
                "security_indicators": ["https", "captcha"]
            }}
            
            Current page HTML:
            {page_source}
            
            Focus on:
            - Semantic HTML structure
            - User interaction patterns
            - Content organization
            - Security features
            """
            
            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     messages=[{
            #         "role": "system",
            #         "content": "You are a web page analyst. Extract structural and functional metadata from HTML."
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.1,
            #     response_format={"type": "json_object"}
            # )
            #system_prompt = "You are a web page analyst. Extract structural and functional metadata from HTML."
            system_prompt = self.prompt_manager.get_prompt("llm_page_analysis", "system")
            self.logger.debug(f"system prompt for page analysis: {system_prompt}")
            user_prompt_template = self.prompt_manager.get_prompt("llm_page_analysis", "user")
            # Format with actual values
            user_prompt = user_prompt_template.format(
                page_source=page_source  # Preserve formatting
            )
            # user_prompt = self.prompt_manager.get_prompt("llm_page_analysis", "user").format(
            #     page_source=page_source
            # )
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            #result = response.choices[0].message.content
            self.logger.info("LLM analysis of current page completed")
            self.logger.debug(f"Raw LLM response: {result}")
            try:
                # Extract JSON from potential text explanation
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()

                self.logger.debug(f"Sanitized LLM response: {json_str}")
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {str(e)}")
                return {}
            
        except Exception as e:
            self.logger.error(f"LLM page analysis failed: {str(e)}")
            return {}
    
    def extract_forms(self):
        forms = []
        for form in self.driver.find_elements(By.TAG_NAME, 'form'):
            form_data = {
                "id": form.get_attribute('id'),
                "action": form.get_attribute('action'),
                "method": form.get_attribute('method'),
                "inputs": [],
                "buttons": []
            }
            for inp in form.find_elements(By.TAG_NAME, 'input'):
                form_data["inputs"].append({
                    "type": inp.get_attribute('type'),
                    "name": inp.get_attribute('name'),
                    "id": inp.get_attribute('id')
                })
            for btn in form.find_elements(By.TAG_NAME, 'button'):
                form_data["buttons"].append({
                    "type": btn.get_attribute('type'),
                    "text": btn.text,
                    "id": btn.get_attribute('id')
                })
            forms.append(form_data)
        return forms
    
    def extract_interactive_elements(self):
        return [{
            "tag": el.tag_name,
            "text": el.text[:50],
            "id": el.get_attribute('id'),
            "type": el.get_attribute('type')
        } for el in self.driver.find_elements(By.CSS_SELECTOR, 'button, a, input, select, textarea')]
    
    def extract_data_tables(self):
        return [{
            "id": table.get_attribute('id'),
            "headers": [th.text for th in table.find_elements(By.TAG_NAME, 'th')],
            "row_count": len(table.find_elements(By.TAG_NAME, 'tr'))
        } for table in self.driver.find_elements(By.TAG_NAME, 'table')]
    
    def identify_key_flows(self):
        return {
            "main_navigation": [a.get_attribute('href') for a in 
                              self.driver.find_elements(By.CSS_SELECTOR, 'nav a, .menu a')[:5]],
            "primary_actions": [btn.text for btn in 
                               self.driver.find_elements(By.CSS_SELECTOR, '.primary-btn, .cta-button')]
        }
    

    def load_test_data(self, file_path="auth_test_data.json"):
        try:
            with open(file_path) as f:
                data = json.load(f)
                
            #validate(data, AUTH_DATA_SCHEMA)
            return data
        except Exception as e:
            self.logger.error(f"Failed to load test data: {str(e)}")
            return None


    def generate_page_specific_tests(self, page_metadata, page_source):
        # Remove schema from prompt to prevent LLM from echoing it back
        """Generate context-aware test cases based on page content for both base functionality and authentication"""
        test_data = None
        # prompt_suffix = ""
        prompt_suffix_new = ""
        # Get prompt suffix templates from YAML
        suffix_templates = self.prompt_manager.get_prompt("generate_tests", "prompt_suffix")

        # Condition 1: Handle auth/contact form test data
        if page_metadata.get('auth_requirements', {}).get('auth_required') or page_metadata.get('contact_form_fields'):
            test_data = self.load_test_data()
            if test_data:
                # Format test_data template from YAML
                test_data_suffix = suffix_templates["test_data"].format(
                    test_data=json.dumps(test_data, indent=2),
                    auth_requirements=json.dumps(page_metadata.get('auth_requirements', {}), indent=2)
                )
                prompt_suffix_new += test_data_suffix

        # Condition 2: Add contact form fields
        if page_metadata.get('contact_form_fields'):
            contact_form_suffix = suffix_templates["contact_form"].format(
                contact_form_fields=json.dumps(page_metadata['contact_form_fields'][0]['fields'], indent=2)
            )
            prompt_suffix_new += contact_form_suffix

        # # Load and format test data if auth required
        # if page_metadata.get('auth_requirements', {}).get('auth_required') or page_metadata.get('contact_form_fields'):
        #     test_data = self.load_test_data()
        #     if test_data:
        #         prompt_suffix = f"""
        #         Available Test Data:
        #         {json.dumps(test_data, indent=2)}
                
        #         For authentication tests:
        #         - Use EXACT values from 'valid' credentials for positive tests
        #         - Use 'invalid' values for negative tests
        #         - Follow field-specific validation rules
        #         - Also test missing values or inputs in required fields for negative tests

        #         Usage Rules for contact_form data (if applicable):
        #         - For contact forms use EXACT values from 'contact_form.valid' for positive tests
        #         - Use 'contact_form.invalid' for negative tests
        #         - Follow field-specific validation rules
        #         - Also test missing values or inputs in required fields for negative tests

        #         Authentication Requirements: 
        #         {json.dumps(page_metadata.get('auth_requirements', {}), indent=2)}
        #         """

        # # Add contact form fields to prompt
        # if page_metadata.get('contact_form_fields'):
        #     prompt_suffix += f"""
        #     When testing for negative cases on contact form fields, properly look for error messages which exist on the page for the respective fields.
        #     Contact Form Fields:
        #     {json.dumps(page_metadata['contact_form_fields'], indent=2)}
        #     """

        # prompt = f"""Generate test cases in VALID JSON format with specific actual current page elements.
        # Generate comprehensive test cases including both regular and authentication tests.
        # Output ONLY valid JSON using this EXACT structure:
        # {{
        #     "test_cases": [
        #         {{
        #             "name": "Test name",
        #             "type": "functional|auth-positive|auth-negative",
        #             "steps": ["step1", "step2"],
        #             "selectors": {{
        #                 "element1": "css_selector",
        #                 "element2": "xpath"
        #             }},
        #             "validation": "Expected outcome",
        #             "test_data": {{
        #                 "field_name": "specific_value"
        #             }}
        #         }}
        #     ]
        # }}
        
        # Current page elements (Page Structure Metadata):
        # {json.dumps(page_metadata, indent=2)}

        # {prompt_suffix}

        # Use selectors from this page structure:
        # {{
        # "title": "{page_metadata['title']}",
        # "forms": {json.dumps(page_metadata['forms'])},
        # "buttons": {json.dumps(page_metadata['buttons'])}
        # }}

        # Current page URL: {page_metadata['url']}
        # Current Page HTML: {page_source}
         
        # Guidelines:
        # 1. Create tests SPECIFIC to these page elements
        # 2. Functional tests for core page elements
        # 3. Cover functional, UI consistency checks, and security aspects
        # 4. Prioritize main user flows
        # 5. Include edge cases for observed input types
        # 6. Include both positive and negative test cases to test functionality
    	 
        # Focus on:
        # - Form validation rules
        # - Navigation consistency
        # - Data presentation integrity
        # - Interactive element functionality
        # - Security considerations
        
        # Rules:
        # 1. Never add comments or explanations
        # 2. Validate JSON before responding
        # 3. Use actual selectors from page metadata
        # 4. For auth tests (if applicable), reference EXACT values from provided test data
        # 5. Auth tests (if auth required):
        #     - Valid credential submission
        #     - Invalid format tests
        #     - Missing required fields
        #     - Security validations
        # 6. Include both positive and negative cases
        
        # Return test cases in specified valid JSON format with Selenium selectors."""
        
        try:
            self.logger.info("Sending request to LLM for test case generation...")
            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     #response_format={"type": "json_object"},
            #     messages=[{
            #         "role": "system", 
            #         "content": "You are a senior QA engineer. Output MUST be valid JSON format as specified. Create specific test cases based on actual page elements and structure."
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.1
            # )
            #return self._parse_test_cases(response.choices[0].message.content)
            # system_prompt = """You are a senior QA engineer. Output MUST be valid JSON format as specified. Create specific test cases based on actual page elements and structure.
            # Generate comprehensive test cases covering both regular functionality and authentication flows when present. 
            # Generate test cases using actual authentication test data only when needed and available.
            # Ensure valid JSON output."""
            system_prompt = self.prompt_manager.get_prompt("generate_tests", "system")
            # user_prompt = self.prompt_manager.get_prompt("generate_tests", "user").format(
            #     page_metadata=json.dumps(page_metadata, indent=2),
            #     prompt_suffix=prompt_suffix,
            #     title=page_metadata['title'],
            #     forms=json.dumps(page_metadata['forms']),
            #     buttons=json.dumps(page_metadata['buttons']),
            #     url=page_metadata['url'],
            #     page_source=page_source
            # )
            user_prompt_template = self.prompt_manager.get_prompt("generate_tests", "user")
            # Format with dynamic values
            user_prompt = user_prompt_template.format(
                page_metadata=json.dumps(page_metadata, indent=2),
                prompt_suffix=prompt_suffix_new,
                title=page_metadata['title'],
                forms=json.dumps(page_metadata['forms']),
                buttons=json.dumps(page_metadata['buttons']),
                interactive_elements = json.dumps(page_metadata['interactive_elements']),
                ui_validation_indicators = json.dumps(page_metadata['ui_validation_indicators']),
                url=page_metadata['url'],
                page_source=page_source
            )
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            #result = response.choices[0].message.content
            self.logger.debug(f"Raw LLM response: {result}")
            self.logger.info("Received response from LLM")
            try:
                # Extract JSON from potential text explanation
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()
                
                #test_cases = json.loads(json_str)
                parsed = json.loads(json_str)
                test_cases = parsed['test_cases']
                #self.logger.info(f"Successfully parsed {len(test_cases.get('test_cases', []))} test cases")
                self.logger.info(f"Successfully parsed {len(test_cases)} test cases")
                
                # Log the test cases for debugging
                # for tc in test_cases.get('test_cases', []):
                #     self.logger.info(f"Generated test case: {tc['id']} - {tc['name']} ({tc['type']})")
                self.logger.debug("Test Case Details:\n" + json.dumps(test_cases, indent=2))

                # Validate test data usage
                if test_data:
                    self._validate_auth_test_data_usage(parsed.get('test_cases', []), test_data)
                
                return test_cases

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON for test cases: {str(e)}")
                self.logger.debug(f"Raw response: {result}")
                return {"test_cases": []}
        except Exception as e:
            self.logger.error(f"Test generation failed: {str(e)}")
            return []
        
    def _validate_auth_test_data_usage(self, test_cases, test_data):
        """Ensure generated auth tests use provided test data"""
        for tc in test_cases:
            if 'auth' in tc.get('type', ''):
                if not self._contains_test_data_values(tc, test_data):
                    self.logger.debug(f"Test case '{tc['name']}' doesn't use provided test data")
                else:
                    self.logger.debug(f"Test case '{tc['name']}' has properly used provided test data")
    
    def _contains_test_data_values(self, test_case, test_data):
        """Check if test case uses appropriate values from test data for credentials, contact_form, or registration_fields"""
        test_fields = set(test_case['test_data'].keys())
        
        # Iterate through each section in test_data
        for section in test_data:
            if section == 'registration_fields':
                # For registration_fields, fields are the top-level keys
                fields = set(test_data['registration_fields'].keys())
                if test_fields <= fields:
                    # Validate each field value against allowed values
                    for field in test_fields:
                        allowed_values = (
                            test_data['registration_fields'][field]['valid'] +
                            test_data['registration_fields'][field]['invalid'] +
                            [""]
                        )
                        if test_case['test_data'][field] not in allowed_values:
                            return False
                    return True
            elif 'valid' in test_data[section] and isinstance(test_data[section]['valid'], dict):
                # For credentials and contact_form, fields are keys in the 'valid' dictionary
                fields = set(test_data[section]['valid'].keys())
                if test_fields <= fields:
                    # Validate each field value against allowed values
                    for field in test_fields:
                        allowed_values = [
                            test_data[section]['valid'][field],
                            test_data[section]['invalid'][field],
                            ""
                        ]
                        if test_case['test_data'][field] not in allowed_values:
                            return False
                    return True
        
        # Return False if no matching section is found
        return False
        
    # def generate_page_specific_tests(self, page_metadata, page_source):
    #     # Existing test generation
    #     base_tests = self.generate_page_specific_base_tests(page_metadata, page_source)
        
    #     # Auth-specific tests
    #     auth_tests = []
    #     if page_metadata.get('auth_requirements', {}).get('auth_required'):
    #         test_data = self.load_test_data()
    #         auth_tests = self._generate_auth_tests(page_metadata, test_data)
        
    #     return base_tests + auth_tests

    def generate_script_for_test_case(self, test_case, page_metadata, page_source):
        captcha_wait_time = self.wait_time or "30 seconds"
        # prompt = f"""Generate Python Selenium script for the following test cases:
        # {json.dumps(test_case, indent=2)}
        
        # Page Structure:
        # {json.dumps(page_metadata, indent=2)}

        # Current page HTML:
        # {page_source}
        
        # Use reliable selectors from page structure.
        # IMPORTANT - Use EXACTLY this WebDriver setup for Selenium 4.15.2:
        # ```
        # from selenium import webdriver
        # from selenium.webdriver.chrome.service import Service
        # from webdriver_manager.chrome import ChromeDriverManager
        
        # # This is the correct way to initialize Chrome in Selenium 4.15.2
        # service = Service(ChromeDriverManager().install())
        # driver = webdriver.Chrome(service=service)
        # ```
        
        # DO NOT use: webdriver.Chrome(ChromeDriverManager().install()) directly as it will cause errors

        # **Before starting any test steps, wait for all JavaScript and AJAX on the page to finish loading.**
        # - Use a robust method such as:
        #     - Waiting for `document.readyState == 'complete'`
        #     - Waiting for jQuery/AJAX activity to finish if present

        # Include CAPTCHA handling when present:
        #     1. Security Features: {page_metadata.get('security_indicators', [])}
        #     2. Check for common CAPTCHA selectors (#captcha, .g-recaptcha, etc.)
        #     3. If CAPTCHA detected:
        #         - Print clear instructions for manual solving
        #         - Pause execution for 2 minutes (120 seconds)
        #         - Add timeout exception handling

        # Return ONLY executable Python code in markdown format.
        # Return ONLY CODE in markdown blocks. No explanations.
        # """
        
        try:
            # response = self.client.chat.completions.create(
            #     model=self.selenium_model,
            #     messages=[{
            #         "role": "system", 
            #         "content": """You are a senior Selenium automation engineer specializing in creating robust, reliable test scripts for Selenium 4.15.2. Generate executable Selenium code using provided selectors. Output ONLY valid Python code in markdown blocks. You write code that:
            #             - Uses best practices for element selection
            #             - Uses the correct WebDriver initialization pattern for Selenium 4.15.2
            #             - Implements proper waits and synchronization
            #             - Handles errors gracefully with retries
            #             - Includes detailed logging and reporting
            #             - Is specific to the website being tested, not generic"""
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.2
            # )
            # Extract first Python code block
            #code_block = extract_first_code(response.choices[0].message.content)
            # if not code_block or code_block.language != "python":
            #     raise ValueError("No valid Python code block found")
            
            #return self._extract_code(response.choices[0].message.content)
            #script_content = self._extract_code(response.choices[0].message.content)
            #script_content= response.choices[0].message.content
            # system_prompt = """You are a senior Selenium automation engineer specializing in creating robust, reliable test scripts for Selenium 4.15.2. Generate executable Selenium code using provided selectors. Output ONLY valid Python code in markdown blocks. You write code that:
            #             - Uses best practices for element selection
            #             - Uses the correct WebDriver initialization pattern for Selenium 4.15.2
            #             - Waits for all JavaScript and AJAX on the page to load before starting any test steps
            #             - For CAPTCHA-protected pages:
            #                 - Detect CAPTCHA elements using common selectors
            #                 - Pause execution for manual solving when CAPTCHA is present
            #                 - Add clear console instructions for user intervention
            #             - Implements proper waits and synchronization
            #             - Handles errors gracefully with retries
            #             - Includes detailed logging and reporting
            #             - Is specific to the website being tested, not generic"""

            # system_prompt = self.prompt_manager.get_prompt("generate_script", "system", tool=self.testing_tool)
            system_prompt_template = self.prompt_manager.get_prompt("generate_script", "system", tool=self.testing_tool)
            system_prompt = system_prompt_template.format(selenium_version=self.selenium_version, language=self.language)
            ## For Puppeteer-2.0.0:
            # system_prompt = system_prompt_template.format(language=self.language)
            self.logger.debug(f"system prompt for script generation: {system_prompt}")
            user_prompt_template = self.prompt_manager.get_prompt("generate_script", "user", tool=self.testing_tool)
            # user_prompt = self.prompt_manager.get_prompt("generate_script", "user").format(
            #     test_case=json.dumps(test_case, indent=2),
            #     page_metadata=json.dumps(page_metadata, indent=2),
            #     page_source=page_source,
            #     security_indicators=page_metadata.get('security_indicators', [])
            # )
            # Format with dynamic values
            user_prompt = user_prompt_template.format(
                language=self.language,
                selenium_version=self.selenium_version,
                test_case=json.dumps(test_case, indent=2),
                page_metadata=json.dumps(page_metadata, indent=2),
                page_source=page_source,
                captcha_wait_time=captcha_wait_time,
                security_indicators=page_metadata.get('security_indicators', [])
            )
            script_content= self.llm.generate(system_prompt, user_prompt, model_type="selenium")
            self.logger.debug(f"Raw LLM response generated code: {script_content}")
            # Extract just the Python code if it's wrapped in markdown code blocks
            if "```python" in script_content:
                code = script_content.split("```python")[1].split("```")[0].strip()
            elif "```java" in script_content:
                code = script_content.split("```java")[1].split("```")[0].strip()
            elif "```" in script_content:
                code = script_content.split("```")[1].strip()
            else:
                code = script_content.strip()
            # Save script to file
            if code:
                # Validate script contains required components
                # required_patterns = [
                #     r"from selenium\.webdriver\.common\.by import By",
                #     r"driver\.(find_element|wait)",
                #     r"assert"
                # ]
                # if not all(re.search(pattern, script_content) for pattern in required_patterns):
                #     raise ValueError("Invalid script structure")
                # required_patterns = [
                #     r'from\s+selenium\s+import',
                #     r'webdriver\.Chrome',
                #     r'find_element\(By\.'
                # ]
                # if not all(re.search(p, script_content) for p in required_patterns):
                #     raise ValueError("Invalid Selenium script structure")
                
                script_dir = "test_scripts"
                if not os.path.exists(script_dir):
                    os.makedirs(script_dir)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if "```python" in script_content:
                    script_name = f"{script_dir}/test_{timestamp}_{test_case['name'].replace(' ', '_')}.py"
                else:
                    script_name = f"{script_dir}/test_{timestamp}_{test_case['name'].replace(' ', '_')}.java"

                with open(script_name, 'w') as f:
                    f.write(code)
                    
                self.logger.info(f"Saved test script: {script_name}")

            return code
            
        except Exception as e:
            self.logger.error(f"Script generation failed: {str(e)}")
            return ""
    
    def track_navigation(self, base_url):
        current_url = self.driver.current_url
        while True:
            try:
                WebDriverWait(self.driver, 30).until(
                    lambda d: d.current_url != current_url
                )
                new_url = self.driver.current_url
                if new_url in self.visited_pages or new_url == base_url:
                    break
                
                self.visited_pages.add(new_url)
                page_analysis = self.analyze_page(context=new_url)
                self.execute_test_cycle(page_analysis)
                current_url = new_url
                
            except TimeoutException:
                self.logger.info("Navigation tracking completed")
                break

    # def execute_test_cycle(self, analysis):
    #     for script in analysis['scripts']:
    #         result = self.execute_test_script(script)
    #         self._log_test_result(result)
    #         if not result['success']:
    #             self._handle_test_failure(result, analysis['metadata'])

    def execute_test_cycle(self, analysis):
        for script in analysis['scripts']:
            if not self.validate_script_structure(script):
                continue
                
            result = self.execute_test_script(script)
            self._log_test_result(result)

    def validate_script_structure(self, script):
        required_imports = ['from selenium import webdriver', 'By']
        return all(imp in script for imp in required_imports)

    def _execute_auth_test(self, script, test_data):
        try:
            # Dynamically insert test data
            formatted_script = script.format(
                valid_user=test_data['credentials']['valid']['username'],
                invalid_pass=test_data['credentials']['invalid']['password']
            )
            return self._run_script(formatted_script)
        except KeyError as e:
            self.logger.error(f"Missing test data: {str(e)}")
            return {"success": False, "error": "Missing test data"}

    def execute_test_script(self, script):
        try:
            # Validate script content
            if not script.strip():
                return {'success': False, 'error': 'Empty test script'}
                
            # Create temporary file for execution
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
                f.write(script)
                temp_file = f.name
                
            # Execute using subprocess
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Test execution timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        
    def _log_test_result(self, result):
        self.test_results.append({
            'timestamp': datetime.now().isoformat(),
            'url': self.driver.current_url,
            'result': result
        })

    def _handle_test_failure(self, result, metadata):
        self.logger.error(f"Test failed: {result.get('error', 'Unknown error')}")
        screenshot = self.capture_screenshot()
        self.logger.info(f"Screenshot captured: {screenshot[:50]}...")
        self.logger.debug(f"Page metadata at failure: {json.dumps(metadata)}")

    def generate_report(self):
        report = {
            'start_time': datetime.now().isoformat(),
            'pages_visited': list(self.visited_pages),
            'test_results': self.test_results,
            'success_rate': len([r for r in self.test_results if r['result']['success']]) / len(self.test_results) if self.test_results else 0,
            'generated_scripts': [f for f in os.listdir('test_scripts') if f.endswith('.py')]
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/test_report_{timestamp}.json"
        
        if not os.path.exists('reports'):
            os.makedirs('reports')
            
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report_file

    def _requires_login(self):
        """Use LLM to check if login/registration is required"""
        try:
            #page_html = self.driver.page_source[:5000]
            page_html = self.driver.page_source
            prompt = f"""Analyze this HTML page and respond ONLY with JSON: 
            {{ "requires_auth": boolean }} 
            Does this page contain login/registration forms or auth requirements?
            Page URL: {self.driver.current_url}
            Partial HTML: {page_html}"""

            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     messages=[{
            #         "role": "system",
            #         "content": "You are an authentication detector. Return JSON with 'requires_auth' boolean."
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.1,
            #     response_format={"type": "json_object"}
            # )
            #system_prompt = "You are an authentication detector. Return JSON with 'requires_auth' boolean."
            system_prompt = self.prompt_manager.get_prompt("requires_auth", "system")
            user_prompt_template = self.prompt_manager.get_prompt("requires_auth", "user")
            # Format prompt with dynamic values
            user_prompt = user_prompt_template.format(
                url=self.driver.current_url,
                page_html=page_html
            )
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            try:
                # Extract JSON from potential text explanation
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()

                parsed= json.loads(json_str)
                self.logger.debug(f"Sanitized LLM response for login/signup check: {parsed}")
                return parsed.get('requires_auth', False)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {str(e)}")
                return {}
            #result = json.loads(response.choices[0].message.content)
            #return result.get('requires_auth', False)
            
        except Exception as e:
            self.logger.error(f"LLM auth check failed: {str(e)}, using fallback")
            # Fallback to element detection
            return any([
                self.element_exists(By.CSS_SELECTOR, "input[type='password'], #login, #signup, #register"),
                self.element_exists(By.XPATH, "//*[contains(text(), 'Log in') or contains(text(), 'Sign up')]")
            ])
    
    def element_exists(self, by, value):
        try:
            self.driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False
        
    ## <--- This version of run_workflow function analyzes one single page at a time --->
    def run_workflow(self, url, username=None, password=None):
        self.driver.get(url)
        
        # if self._requires_login():
        #     if not username or not password:
        #         raise ValueError("Login required but credentials not provided")
        #     self.login_to_website(url, username, password)
        
        initial_analysis = self.analyze_page(context=url)
        self.execute_test_cycle(initial_analysis)
        self.track_navigation(url)
        
        self.driver.quit()
        return self.generate_report()


    ## <--- Uncomment this version of run_workflow function to perform recursive url extraction and integrated testing --->
    # def run_workflow(self, base_url, username=None, password=None):
    #     """Enhanced workflow with recursive URL discovery"""
    #     try:
    #         # Extract URLs first
    #         # Extract URLs with 2-level recursion
    #         all_urls = self.url_extractor.extract_urls(base_url, max_depth=1)
    #         if not all_urls:
    #             self.logger.warning("No URLs found to test")
    #             return self.generate_report()

    #         # Process each URL
    #         for url in all_urls:
    #             self.process_single_url(url, username, password)
                
    #         return self.generate_report()
            
    #     finally:
    #         self.driver.quit()

    # def process_single_url(self, url, username, password):
    #     """Process individual URL with existing workflow"""
    #     self.logger.info(f"\n{'='*50}")
    #     self.logger.info(f"Processing URL: {url}")
        
    #     self.driver.get(url)
        
    #     # if self._requires_login():
    #     #     if not username or not password:
    #     #         raise ValueError("Login required but credentials not provided")
    #     #     self.login_to_website(url, username, password)
            
    #     #analysis = self.analyze_page(url)
    #     analysis = self.analyze_page(context=url)
    #     self.execute_test_cycle(analysis)
    #     self.track_navigation(url)

    ## Dynamic with LLM Analysis
    def login_to_website(self, url, username=None, password=None):
        """Perform dynamic login/registration with user input for additional fields"""
        if not username or not password:
            raise ValueError("Credentials required for authentication")
            
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            #page_html = self.driver.page_source[:10000]
            page_html = self.driver.page_source
            prompt = f"""Extract auth form selectors as JSON:
            {{
                "username_selector": "css_selector", 
                "password_selector": "css_selector",
                "submit_selector": "css_selector",
                "auth_type": "login|registration",
                "additional_fields": {{
                    "field_name": {{
                        "selector": "css_selector",
                        "type": "text|email|tel|date"
                    }}
                }}
            }}
            Current page HTML: {page_html}"""

            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     messages=[{
            #         "role": "system",
            #         "content": "You are a web form analyzer. Return JSON with auth form selectors and field types."
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.1,
            #     response_format={"type": "json_object"}
            # )
            #system_prompt= "You are a web form analyzer. Return JSON with auth form selectors and field types."
            system_prompt = self.prompt_manager.get_prompt("auth_form_selectors", "system")
            user_prompt_template = self.prompt_manager.get_prompt("auth_form_selectors", "user")
            # Format prompt with dynamic values
            user_prompt = user_prompt_template.format(
                page_html=page_html
            )
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            
            #auth_data = json.loads(response.choices[0].message.content)
            try:
                # Extract JSON from potential text explanation
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()

                self.logger.debug(f"Sanitized LLM response: {json_str}")
                auth_data= json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {str(e)}")
                return {}
            #auth_data = json.loads(result)
            self.logger.debug(f"Auth form structure: {json.dumps(auth_data, indent=2)}")

            # Fill credentials
            self.driver.find_element(By.CSS_SELECTOR, auth_data['username_selector']).send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, auth_data['password_selector']).send_keys(password)

            # Handle additional fields
            if 'additional_fields' in auth_data:
                field_values = {}
                for field_name, field_info in auth_data['additional_fields'].items():
                    while True:
                        value = input(f"Enter {field_name} ({field_info.get('type', 'text')}): ")
                        if self.validate_field_input(value, field_info.get('type')):
                            field_values[field_name] = value
                            break
                        print(f"Invalid format for {field_name}. Please try again.")
                    
                    self.driver.find_element(By.CSS_SELECTOR, field_info['selector']).send_keys(field_values[field_name])

            # Submit form
            self.driver.find_element(By.CSS_SELECTOR, auth_data['submit_selector']).click()
            
            WebDriverWait(self.driver, 10).until(
                lambda d: d.current_url != url
            )
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse auth selectors: {str(e)}")
            raise RuntimeError("Failed to analyze login form structure")
        except NoSuchElementException as e:
            self.logger.error(f"Auth element not found: {str(e)}")
            raise RuntimeError("Authentication elements missing on page")
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise

    def validate_field_input(self, value, field_type):
        """Basic validation for different field types"""
        if not value:
            return False
            
        if field_type == "email":
            return '@' in value and '.' in value.split('@')[-1]
        elif field_type == "tel":
            return value.replace(' ', '').replace('-', '').isdigit()
        elif field_type == "date":
            return bool(re.match(r'\d{4}-\d{2}-\d{2}', value))
        return True

from urllib.parse import urlparse, urljoin

class URLExtractor:
    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)
        
    def extract_urls(self, base_url, max_depth=2):
        """Recursively extract unique internal URLs with BFS up to max_depth"""
        self.logger.info(f"Starting recursive URL extraction from: {base_url}")
        
        try:
            parsed_base = urlparse(base_url)
            base_domain = parsed_base.netloc
            visited = set()
            to_visit = [(base_url, 0)]  # (url, depth)

            while to_visit:
                current_url, depth = to_visit.pop(0)
                
                if current_url in visited or depth > max_depth:
                    continue
                
                try:
                    self.logger.debug(f"Waiting 1 sec. before processing {current_url}")
                    time.sleep(1)
                    self.driver.get(current_url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'body'))
                    )
                    visited.add(current_url)
                    self.logger.info(f"Processing depth {depth}: {current_url}")

                    # Extract links from current page
                    links = self.driver.find_elements(By.TAG_NAME, 'a')
                    new_urls = set()

                    for link in links:
                        href = link.get_attribute('href')
                        if not href:
                            continue
                            
                        full_url = urljoin(current_url, href)
                        parsed_url = urlparse(full_url)
                        
                        if parsed_url.netloc == base_domain:
                            # Normalize path and handle root URL
                            path = parsed_url.path.rstrip('/') or '/'
                            #clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}".rstrip('/')
                            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{path}"
                            if clean_url not in visited:
                                new_urls.add(clean_url)

                    # Add discovered URLs to queue
                    for url in new_urls:
                        if url not in [u for u, _ in to_visit]:
                            to_visit.append((url, depth + 1))
                            
                    self.logger.debug(f"Found {len(new_urls)} new URLs at depth {depth}")

                except Exception as e:
                    self.logger.error(f"Failed to process {current_url}: {str(e)}")

            self.logger.info(f"Total unique URLs found: {len(visited)}")

            for url in visited:
                self.logger.debug(f"Found URL: {url}")

            return sorted(visited)
            
        except Exception as e:
            self.logger.error(f"URL extraction failed: {str(e)}")
            return []
        

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Automated Website Testing Agent")
#     parser.add_argument("--url", required=True, help="Website URL to test")
#     parser.add_argument("--username", help="Login username")
#     parser.add_argument("--password", help="Login password")
#     parser.add_argument("--loglevel", "-l", 
#                         default="INFO",
#                         choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
#                         help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
#     args = parser.parse_args()

#     tester = WebTestGenerator(log_level=args.loglevel)
#     report_file = tester.run_workflow(args.url, args.username, args.password)
#     print(f"Test report generated: {report_file}")

# Main execution
if __name__ == "__main__":
    # Initialize the generator
    generator = WebTestGenerator(log_level="INFO")
    
    # Generate scripts for each test case
    for test_case in test_cases:
        script = generator.generate_script_for_test_case(test_case, page_metadata, page_source)
        print(f"Generated script for '{test_case['name']}':\n{script}\n")