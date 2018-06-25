# ACM Auto Validation

AWS ACM Auto Valudation is a tool for adding more convenience to your [AWS CloudFormation](https://aws.amazon.com/cloudformation/) templates, and SAM deployments.  It will also the creation of fully issues Certificates in ACM that autorenew.

### Installation

Execute the shell script to deploy the AWS Lambda Function.  Once installed the ARN of the Lambda Function is exported so that it can be used by other CloudFormation Stacks to generate certificates.

```shell
./install.sh mybucket
```

### Example CloudFormation template

The following example creates a new Certificate in ACM that will be automatically validated.

```yaml
Description: Creates a ACM Certificate and automatically registers . Outputs the ACM ARN.

Resources:
  ACMCertificate:
    Type: Custom::ACMAutoValidate
    Properties:
      ServiceToken: !ImportValue ACMAutoValidate
      FQDN: host.example.com

Outputs:
  ACMCertificateARN:
    Description: ACM Certificate ARN
    Value: !GetAtt ACMCertificate.Arn
```
