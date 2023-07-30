# Week X - Clean up

It's ~~over~~ good enough!

## IAM DB Authentication

The biggest issue was the post-confirmation Lambda breaking after I stopped hardcoding the database password and instead tried to fetch the username, password, and endpoint at lambda runtime. The fetch worked for other uses (ECS service, Gitpod), but the Lambda was running in my VPC and didn't have internet access, so the SSM fetch stalled, resulting in the lambda timing out.

I tried a few things:

1. Adding an egress-only internet gateway didn't resolve the problem
2. Moving the parameters from resolve SSM at runtime to using `{{resolve}}` in CFN as environment variables. The move worked for username and endpoint but failed for the password since that was stored as a `SecureString`, which [CFN only supports resolving for some resources](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references.html#template-parameters-dynamic-patterns-resources).
3. Providing the SSM Parameter as [an input Parameter for the stack with SSM Parameter types](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html#aws-ssm-parameter-types). Failed for the password because `SecureString` isn't supported.

I ended up rewriting the post-confirmation Lambda to use [IAM database authentication](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html), and that worked. I was happy not to have the password hardcoded in any environment variables.

Setting up the IAM Auth was reasonably straightforward. One thing that would make it easier is to have the primary user (specified at DB creation time) automatically have the IAM access grant. (Admittedly, I just went off the docs instead of testing whether or not the primary user had IAM access permissions.) I also had to alter permissions on the existing tables in the DB to give the new user access.

In comparison, needing a specific value exported by the database cloudformation template was far more straightforward.

## But now timeouts?

Except the Lambda was bumping right up against the 3-sec timeout and sometimes got killed.

I used [Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning) to figure out if giving the function more memory (and CPU power) would help, and it did.

The [resulting graph](https://lambda-power-tuning.show/#gAAAAQACAAMABAAIwAs=;VdWCQ1VVcUOrqjdDVdWRQwAANEOrqpZDq6qMQw==;dbETNT1riDVpcs81Leh2Nu3vSjbkPSo3xXtpNw==) claims that leaving the memory at 128MB would be the cheapest, but I chose the "Best Time" value of 1024MB instead.

## Love affair with SSM

I initially viewed SSM as environment variables on steroids, but they are significantly more helpful than I expected in CloudFormation.

ECS secrets have `ValueFrom` that pulls the value of SecureStrings in; I can use SSM values as parameters to a CloudFormation stack; CloudFormation itself [resolve parameter values at execution time](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/dynamic-references.html#dynamic-references-ssm).

Because CloudFormation can set a Parameter as a resource, I can use the set/resolve combination to form an implicit dependency instead of an explicit "depend on this other stack by importing an exported CFN value." There's still an implicit dependency at turnup time because _something_ has to create the parameter, but after that, the first stack can be deleted without interfering with the second stack.

## Calling it done on the frontend feels bad

I'm not too happy with the frontend, there are still CSS bugs, and some things need to be fixed (e.g., notifications are still a fixed return value), but I'm not up to debugging React & CSS.

I ran through Andrew's changes and merged most in - there were a few that I had already done (e.g., some lint fixes).

I also set up and ran eslint (`npx eslint --fix "src/**/*.js"`), which cleaned up a few hundred warnings.
