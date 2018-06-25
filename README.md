# ACM Auto Validation (DNS)

A Lambda Function to automate the creation of Certificates in AWS ACM with DNS Validation.  AWS ACM Auto Valudation is a tool for adding more convenience to your [AWS CloudFormation](https://aws.amazon.com/cloudformation/) templates, and [SAM deployments](https://aws.amazon.com/about-aws/whats-new/2016/11/introducing-the-aws-serverless-application-model/). By automating the process of DNS validation into CloudFormation you are covered by the automatic renewal of the certificates through DNS CNAME validation.

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
      domainname: host.example.com
      additionalnames:
        - www.example.com

Outputs:
  ACMCertificateARN:
    Description: ACM Certificate ARN
    Value: !GetAtt ACMCertificate.Arn
```
