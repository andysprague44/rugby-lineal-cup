#!/bin/bash

# aws sso login --profile andysprague44
# export AWS_PROFILE=andysprague44

# deploy html files to s3 bucket
for f in $(find ./web_static -type f); do
    aws s3 cp $f s3://www.rugbylinealworldtitledata.com/$(basename $f)
done

# invalidate in cloudfront to refresh cache
aws cloudfront create-invalidation --distribution-id E3UX699K30BAAY --paths "/*" >> /dev/null
aws cloudfront create-invalidation --distribution-id E31LF1TE1RDZ98 --paths "/*" >> /dev/null
