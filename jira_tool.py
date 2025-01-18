from crewai.tools import tool
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import os
import json

@tool
def jira_issue_fetcher(project_key: str) -> List[Dict[str, Any]]:
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
  return json.dumps(data)
