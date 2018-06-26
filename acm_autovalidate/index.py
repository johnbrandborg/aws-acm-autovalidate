"""
ACM Certificate with DNS Validation - AWS Lambda Function Index File
Contains the handler function that is used to execute the Lambda Function
"""

import traceback
import boto3
import time
from .helper import responder

def handler(event, context):
    """
    CloudFormation Custom Resource Logic
    """
    print(f"Event: {event}")

    # Setup Clients
    acm_client = boto3.client("acm")
    route53_client = boto3.client("route53")

    # Create a temporary PhysicalResourceId until the Certificate ARN is created and can be used instead
    if event["RequestType"] == "Create":
        event["PhysicalResourceId"] = context.aws_request_id
 
    print("Checking for requiremented properties and set variables")
    properties = event.get("ResourceProperties", {})
    if "domainname" not in properties:
        return responder(event, context, "FAILED", f"Missing parameter(s): {domainname}")
    domainname = properties["domainname"].rstrip(".")
    domain = ".".join(domainname.split(".")[1:])
    additionalnames = [
        name.rstrip(".") for name in properties["additionalnames"]
    ] if "additionalnames" in properties else None

    print(f"Checking if the domain exists and gather ZoneID for {domain}")
    hosted_zones = route53_client.list_hosted_zones_by_name(DNSName = domain)["HostedZones"]
    if len(hosted_zones) > 1:
        return responder(event, context, "FAILED", "Domainname is not specific enough to determine the Hosted Zone ID") 
    else:
        zone_id = hosted_zones[0]["Id"]

    if event["RequestType"] == "Delete":
        print("Delete Request received. Attempting to remove ACM and Route53 resources")
        try:
            certificate_details = acm_client.describe_certificate(CertificateArn = event["PhysicalResourceId"])
            change_record = [
                {
                    "Action":"DELETE",
                    "ResourceRecordSet": {
                        "Name": options["ResourceRecord"]["Name"],
                        "Type": options["ResourceRecord"]["Type"],
                        "TTL": 3600,
                        "ResourceRecords": [
                            {
                                "Value": options["ResourceRecord"]["Value"]
                            }
                        ]
                    }
                } for options in certificate_details["Certificate"]["DomainValidationOptions"]
            ]
            route53_response = route53_client.change_resource_record_sets(
                HostedZoneId = zone_id,
                ChangeBatch = {
                    "Comment": "DNS Validation",
                    "Changes": change_record
                }
            )
            acm_response = acm_client.delete_certificate(CertificateArn = event["PhysicalResourceId"])
        except:
            traceback.print_exc()
        return responder(event, context)

    print("Create/Update Request received. Attempting to create ACM and Route53 Resources")
    if not event["PhysicalResourceId"].startswith("arn:aws:acm:"):
        print("No ARN listed within the PhysicalRecourseId. Creating a Certificate now.")
        try:
            if additionalnames is None:
                acm_response = acm_client.request_certificate(
                    DomainName = domainname,
                    ValidationMethod = "DNS",
                    IdempotencyToken = event["LogicalResourceId"]
                )
            else:
                acm_response = acm_client.request_certificate(
                    DomainName = domainname,
                    SubjectAlternativeNames = additionalnames,
                    ValidationMethod = "DNS",
                    IdempotencyToken = event["LogicalResourceId"]
                )
        except:
            traceback.print_exc()
        event["PhysicalResourceId"] = acm_response["CertificateArn"]
    else:
        print("Certificate has already been created.  Only the DNS will be processed")

    print("Setting up DNS Validation with options found on {}".format(event["PhysicalResourceId"]))
    exceptions = 0
    while True:
        if exceptions == 3: break
        try:
            certificate_details = acm_client.describe_certificate(CertificateArn = event["PhysicalResourceId"])
            change_record = [
                {
                    "Action":"UPSERT",
                    "ResourceRecordSet": {
                        "Name": options["ResourceRecord"]["Name"],
                        "Type": options["ResourceRecord"]["Type"],
                        "TTL": 3600,
                        "ResourceRecords": [
                            {
                                "Value": options["ResourceRecord"]["Value"]
                            }
                        ]
                    }
                } for options in certificate_details["Certificate"]["DomainValidationOptions"]
            ]
            break
        except:
            exceptions = exceptions + 1
            time.sleep(10)
    try:
        route53_response = route53_client.change_resource_record_sets(
            HostedZoneId = zone_id,
            ChangeBatch = {
                "Comment": "DNS Validation",
                "Changes": change_record
            }
        )
    except:
        traceback.print_exc()
    return responder(event, context, data = {"Arn": event["PhysicalResourceId"]})
