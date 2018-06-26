"""
ACM Certificate with DNS Validation - AWS Lambda Function Index File
Contains the handler function that is used to execute the Lambda Function
"""

import traceback
import boto3
from time import sleep
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
        event["PhysicalResourceId"] = context.invoked_function_arn.split(":").pop()
 
    print("Check for any missing requirements and setup variables")
    properties = event.get("ResourceProperties", {})
    missing = [param for param in ("domainname","additionalnames") if param not in properties]
    if missing:
        return responder(event, context, "FAILED", "Missing parameter(s): {}".format(", ".join(missing)))
    domainname = properties["domainname"].rstrip(".")
    domain = ".".join(domainname.split(".")[1:])
    additionalnames = [name.rstrip(".") for name in properties["additionalnames"]]

    print(f"Check if the domain exists and gather ZoneID for {domain}")
    zone_id = route53_client.list_hosted_zones_by_name(DNSName = domain)["HostedZones"][0]["Id"]

    if event["RequestType"] == "Delete":
        print("Delete Request received. Removing resources")
        # Collect the Pending ARN and then gather CNAME details for Validation
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

    print(f"Checking if the certificate has been created for {domainname}")
    certificates = acm_client.list_certificates(
        CertificateStatuses=[
            "PENDING_VALIDATION",
            "ISSUED"
        ]
    )["CertificateSummaryList"]
    certificate_arns = [cert["CertificateArn"] for cert in certificates if cert["DomainName"] == domainname]
    certificate_arn = certificate_arns[0] if len(certificate_arns) == 1 else None

    print("Create/Update Request received. Creating Resources")
    if certificate_arn is None:
        try:
            acm_response = acm_client.request_certificate(
                DomainName = domainname,
                SubjectAlternativeNames = additionalnames,
                ValidationMethod = "DNS",
                IdempotencyToken = event["LogicalResourceId"]
            )
            certificate_arn = acm_response["CertificateArn"]
            sleep(5)
        except:
            traceback.print_exc()

    # Build the change record with any DNS options found on the Certificate
    certificate_details = acm_client.describe_certificate(CertificateArn = certificate_arn)
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

    print("Creating the DNS Validation entry within the Route53 Zone")
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

    event["PhysicalResourceId"] = certificate_arn
    return responder(event, context, data = {"Arn": certificate_arn})
