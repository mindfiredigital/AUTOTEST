import argparse
import sys
from ..core.web_test_generator import WebTestGenerator

def main():
    parser = argparse.ArgumentParser(description="Automated Website Testing Agent")
    parser.add_argument("--url", required=True, help="Website URL to test")
    parser.add_argument("--username", help="Login username")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--loglevel", "-l", 
                        default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set logging level")
    parser.add_argument("--selenium-version", 
                        default="4.15.2",
                        help="Selenium version to use in generated scripts")
    parser.add_argument("--wait-time", 
                        default="",
                        help="Custom wait time text for CAPTCHA handling")
    parser.add_argument("--testing-tool",
                        default="selenium",
                        choices=["selenium", "playwright", "puppeteer"],
                        help="Testing framework to generate scripts for")
    parser.add_argument("--language",
                        default="python",
                        help="Programming language for test scripts")
    
    # New recursive testing arguments
    parser.add_argument("--recursive", "-r",
                       action="store_true",
                       help="Enable recursive URL extraction and testing")
    parser.add_argument("--max-depth",
                       type=int,
                       default=1,
                       help="Maximum depth for recursive URL extraction (default: 1)")
    
    parser.add_argument("--no-cache",
                        action="store_true",
                        help="Disable use of cache memory during testing")
    
    parser.add_argument("--llm-provider",
                    type=int,
                    choices=[1, 2, 3, 4, 5],
                    default=1,
                    help="LLM Provider choice: 1=OpenAI, 2=Groq, 3=Google-Gemini, 4=Anthropic, 5=Ollama")
    
    args = parser.parse_args()
    
    try:
        tester = WebTestGenerator(
            log_level=args.loglevel.upper(), 
            selenium_version=args.selenium_version, 
            wait_time=args.wait_time, 
            testing_tool=args.testing_tool, 
            language=args.language,
            llm_provider_choice=args.llm_provider  # Add this line
        )
    except ValueError as e:
        print(f"Invalid configuration: {str(e)}")
        sys.exit(1)
        
    #report_file = tester.run_workflow(args.url, args.username, args.password, args.no_cache, recursive=args.recursive, max_depth=args.max_depth)
    #print(f"Test report generated: {report_file}")

    report_result = tester.run_workflow(args.url, args.username, args.password, args.no_cache, recursive=args.recursive, max_depth=args.max_depth)
    if args.recursive:
        print(f"Test reports generated ({len(report_result)} files):")
        for i, report_file in enumerate(report_result, 1):
            print(f"  {i}. {report_file}")
    else:
        print(f"Test report generated: {report_result}")

if __name__ == "__main__":
    main()