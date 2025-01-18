from crewai.tools import tool
from typing import Dict,List
import re
import json
import os

# Loading Regular Expression patterns
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "regex.json"), "r") as file:
    regex_patterns = json.load(file)

# Pre-compiling regex patterns
patterns = {name: re.compile(pattern) for name, pattern in regex_patterns['custom_rules'].items()}


def pattern_based_scan(data):
    """
    Scans the input data for matches against precompiled regex patterns.

    :param data: String or list of strings to scan.
    :return: Dictionary of matches by pattern name.
    """
    matches = {}

    if isinstance(data, str):
        for name, pattern in patterns.items():
            match = pattern.findall(data)
            if match:
                matches[name] = match
    elif isinstance(data, list):
        for name, pattern in patterns.items():
            for item in data:
                match = pattern.findall(item)
                if match:
                    matches.setdefault(name, []).extend(match)

    return matches


def keyword_based_search(data):
    """
    Searches for keywords in the input data.

    :param data: String or list of strings to scan.
    :return: Dictionary of matches by keyword.
    """
    matches = {}

    if isinstance(data, str):
        for keyword in regex_patterns['keywords']:
            if keyword in data:
                matches[keyword] = data
    elif isinstance(data, list):
        for keyword in regex_patterns['keywords']:
            for item in data:
                if keyword in item:
                    matches.setdefault(keyword, []).append(item)

    return matches


def collate_matches(data):
    """
    Collates matches from pattern-based and keyword-based searches.

    :param data: String, list of strings, or other iterable data to scan.
    :return: Merged dictionary of matches.
    """
    if not isinstance(data, (str, list)):
        raise ValueError("Invalid data type for scanning. Expected string or list of strings.")

    pattern_matches = pattern_based_scan(data)
    keyword_matches = keyword_based_search(data)
    return {**pattern_matches, **keyword_matches}

@tool
def secret_scanner(data: List) -> List:
    """
    Scans a list of Jira issues for sensitive information.

    :param data: List of dictionaries containing issue data, or a dictionary with a 'data' key.
    :return: List of dictionaries with detected secrets.
    """
    args_schema={
        "data": {
            "type": "object",
            "description": "The input data containing Jira issues. Must be a list with multiple dictionaries or a dictionary with a 'data' key."
        }
    }
    print(f"Received input: {data}")

    if data is None:
        raise ValueError("Missing required input: 'data'.")
    elif isinstance(data, list):
        issues = json.loads(json.dumps(data))
    else:
        raise ValueError("Invalid input format. Expected a list of issues.")
    
    try:
        secrets_found = []
        print("Entering into Try block............")
        for item in issues:
            issue_matches = {"issue_key": item.get('key')}
            if 'description' in item:
                description_matches = collate_matches(item['description'])
                if description_matches:
                    issue_matches['source_description'] = description_matches

            if 'comments' in item:
                comments_matches = collate_matches(item['comments'])
                if comments_matches:
                    issue_matches['source_comments'] = comments_matches

            if 'source_description' in issue_matches or 'source_comments' in issue_matches:
                secrets_found.append(issue_matches)

        print("Scanning is completed .............")
        return json.loads(json.dumps(secrets_found))

    except Exception as e:
        print(f"Error in secret_finder: {e}")
        raise

'''
if __name__ == "__main__":
    # Sample data
    data = [
        {
            "key": "SECBUG-1",
            "description": (
                "This is an issue description containing api_token NTUyNTU1MTU3MTU5OtNuBKZbpJGN3l2u73QXeydLVc6R "
                "used for postman collection testing of Jira access. The pattern matching of the issues is used for "
                "AWS_ACCESS_KEY_ID=AKIAXXXXXXXEXAMPLEAKIAIOSFODNN7EXAMPLE"
            ),
            "comments": [
                "This is a comment to test AWS platform with AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "Hello, the testing is completed"
            ],
        },
        {
            "key": "SECBUG-2",
            "description": (
                "Issue description integrating with Slack channel to post updates to the channel and we are using "
                "the token for the same as SLACK_BOT_TOKEN=xoxb-123456789012-12345678901234-ABCDEFGHIJKLMNO"
            ),
            "comments": [
                "This is a comment to update the issues on progress",
                "Token for the comment is updated here as SLACK_SIGNING_SECRET=abcdef1234567890abcdef1234567890"
            ],
        },
    ]

    # Execute secret finder and print results
    results = secret_finder(data)
    print(json.dumps(results, indent=4))
    '''
