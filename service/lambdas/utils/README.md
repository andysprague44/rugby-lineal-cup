This folder contains shared code across this stack, and is packaged as a 'lambda layer' when deployed to AWS.

The requirements specified in this folder's `requirements.txt` file do not need to be repeated 
in the `requirements.txt` files of the actual lamdba folders.

We also do not need:
- boto3 / botocore: already included in the lambda runtime
- aws-lamdba-powertools: we add powertools dependencies from the pre-packaged lambda layer