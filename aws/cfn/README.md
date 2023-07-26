The `cfn/` and `sam/` folders contain bootstrap scripts to setup cruddur.

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

The S3 bucket created by this is used in sam/presign.yml

## Unmanaged
* ECR repo creation
* Cognito User Pool
* Codestar confirmation with Github

## Turnup order
1. `cfn networking`
2. `cfn frontend`
3. `samcfn bd ddb`
4. `samcfn bd presign-authorizer`
5. `samcfn bd presign`
6. `cfn backend`
7. `cfn service`
8. `cfn db`
9. `cfn cicd`
10. `samcfn bd user-confirm`
