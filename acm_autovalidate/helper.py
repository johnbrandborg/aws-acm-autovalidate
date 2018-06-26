"""
ACM Certificate with DNS Validation - AWS Lambda Function Helper File
Contains Classes and Functions used within the index
"""

import json
from urllib.request import urlopen, Request, HTTPError, URLError

def responder(event, context, status = "SUCCESS", reason = "Not Specified", data = {}):
    """
    CloudFormation Responder
    """
    print(f"Response: {status} Reason: {reason} Data: {data}")

    # Build Response as a PUT Request
    body = {
        "Status": status,
        "Reason": reason,
        "PhysicalResourceId": event["PhysicalResourceId"],
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": data,
    }
    body = json.dumps(body).encode("utf-8")
    put_request = Request(event["ResponseURL"], data = body, headers = {
        "Content-Length": len(body),
        "Content-Type": "",
    })
    put_request.get_method = lambda: "PUT"

    # Send the Web Response
    try:
        urlopen(put_request)
        return True
    except HTTPError as e:
        print(f"Failed executing HTTP request: {e.code}")
        return False
    except URLError as e:
        print(f"Failed to reach the server: {e.reason}")
        return False
