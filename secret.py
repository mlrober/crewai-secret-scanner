from crewai import Agent, Task, Crew, Process
import os
from dotenv import load_dotenv

# Environment setup
os.environ["OTEL_SDK_DISABLED"] = "true"
load_dotenv()

from langchain_openai import ChatOpenAI
from tools.jira_tool import jira_issue_fetcher
from tools.secret_finder import secret_scanner

# Initialize LLM
llm = ChatOpenAI(
    model="ollama/llama3.2",
    openai_api_key=os.environ["OPENAI_API_KEY"],
    base_url="http://localhost:11434/v1"
)

# Define a single agent with modular task capabilities
jira_agent = Agent(
    role='Jira Agent',
    goal="Fetch Jira issues and comments. {project_name}.",
    verbose=True,
    allow_delegation=True,
    memory=False,
    backstory=(
        """
        You're a seasoned researcher with an expertise in jira
    fetch issues and comments from {project_name} project in the defined format in expected output."""
    ),
    llm=llm,
    tools=[jira_issue_fetcher]
)

security_agent = Agent(
    role="Security Analyst",
    goal=(
        "Identify the secrets in jira issues and remove false positives or junk data."
    ),
    verbose=True,  # Enable verbose mode for debugging during development.
    allow_delegation=True,
    memory=False,  # Use memory to store intermediate results or track analysis context.
    backstory=(
        """
        As a security analyst, your responsibility is to identify sensitive information such as api token,
        credentials etc.. You have to review the output of the tool secret-finder for false positives and
        junk data and clean them.
        """
    ),
    llm=llm,  # Language model for generating summaries or reports.
    tools=[secret_scanner]  # Secret-finding tool for identifying sensitive data.
)

# Task definitions
fetch_issues_task = Task(
    description=(
        """1. Strictly  use {project_name} as input to jira_issue_fetcher tool and do not provide your own value.
        2. Send the output without modifying to the next task
        """
    ),
    expected_output="""
        A JSON list of dictionarie in below example format
    
        Example:
    
        [
        {{"key": "Secbug-1", 
         "description": "this is a description",
         "comments": ["comment1", "comment2"]}},
    {{...}}
    """,
    agent=jira_agent,
    output_file="issues.md"
)

secret_scanning_task = Task(
    description=(
        """
        1. Strictly Pass the context given as input to secret-finder tool and do not modify or provide your own data as input
        2. Analyse the output for false positives or junk data and clean them
        """
        ),
    expected_output=(
        """
            A JSON list with dictionaries, where each dictionary contains:
            - `issue_key`: A string representing the unique identifier for the detected issue.
            - `source_description`: A dictionary containing keys representing types of sensitive information (e.g., 'AWS API Key', 'Slack_Token', 'token', etc.) and their respective values as lists of detected items.
            - `source_comments` (optional): A dictionary containing additional comments with keys as categories and values as lists of related sensitive information.

            Example output:
            
            [{{'issue_key': 'key', 'source_description': {{'key': [value], 'key': "value", ...}}, 'issue_comments': {{'key': [value], 'key': "value", ...}}}}]
        """
    ),
    agent=security_agent,
    context=[fetch_issues_task]
)

report_writing_task = Task(
    description=(
        "Generate a detailed and visually appealing report summarizing sensitive data findings in Jira. "
        "Include key metrics (total issues scanned, sensitive data detected, severity levels), a structured table of findings, "
        "impact analysis, data visualizations (e.g., pie charts, bar graphs), and actionable recommendations."
    ),
    expected_output="A Markdown report summarizing the findings and recommendations.",
    agent=security_agent
)

# Crew and process definition
crew = Crew(
    agents=[jira_agent, security_agent],
    tasks=[fetch_issues_task, secret_scanning_task, report_writing_task],
    process=Process.sequential
)

# Kick off the crew with the dynamic project name
result = crew.kickoff(inputs={'project_name': 'SECBUG'})
print(result)
