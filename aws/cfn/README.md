The `cfn/` and `sam/` folders contain bootstrap scripts to setup cruddur.

`bin/cfn` and `bin/samcfn` are helper scripts to trigger CloudFormation and SAM builds respectively

They are currently hard0coded to use the `lightweaver-cfn-artifacts` S3 bucket as an upload target.

## Prereqs
### DNS
Create a Hosted Zone in Route 53 for the domain name
* Provide the hosted zone ID as a parameter to service.yml
* Provide the plain DNS name as a parameter to frontend.yml
* Create a ACM certificate in us-east-1 for the same DNS name

### Secrets
These are all stored as SecureStrings in SSM
* Database password stored at the path `/cruddur/db/password`
* Rollbar Access Token stored at the path `/cruddur/backend-flask/ROLLBAR_ACCESS_TOKEN`
* Honeycomb headers stored at the path `/cruddur/backend-flask/OTEL_EXPORTER_OTLP_HEADERS`

## CDK Managed
Thumbnail creation is managed by CDK, check the folder `thumbing-serverless-cdk`.

The S3 bucket created by this is hardcoded in sam/presign.yml

## Unmanaged
* ECR repo creation
* Cognito User Pool
* Codestar confirmation with Github

## Turnup order
1. No dependencies:
```
cfn networking
cfn frontend
samcfn bd ddb
samcfn bd presign-authorizer
samcfn bd presign
```
2. `cfn backend`
3. `cfn db`
4. `samcfn bd user-confirm`
    * This has dependencies on the Security Group & Database endpoint
5. `cfn service`
6. `cfn cicd`

## Post Turnup
1. [Approve the codestar connection](https://us-west-2.console.aws.amazon.com/codesuite/settings/connections)
2. Push a codepipeline build to populate the frontend bucket
3. Populate the Cruddur database - `db -p init`
    * Run `source update-sg-rule` to populate the `PROD_CONNECTION_URL` if needed
4. Update the cognito user pool post confirmation lambda to point to the created post confirmation lambda
