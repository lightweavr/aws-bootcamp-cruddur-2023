The `cfn/` and `sam/` folders contain bootstrap scripts to setup cruddur.

## Prereqs
* Database password stored as a secure string in SSM at the path `/cruddur/db/password`
* DNS Hosted Zone setup in route 53, provide the hosted zone ID as a parameter to service.yml
    * DNS Name, provide the name as a parameter to frontend.yml
    * ACM certificate in us-east-1 for the same DNS name
*

## CDK Managed
Thumbnail creation is managed by CDK, check the folder `thumbing-serverless-cdk`.

The S3 bucket created by this is used in sam/presign.yml

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
