import json

import boto3
from utils.image_processor import process_and_route_image
from utils.parse_s3_key import parse_s3_key
from utils.size_checker import enforce_project_quota

s3_client = boto3.client("s3")


def lambda_handler(event, context):
    try:
        record = event["Records"][0]
        bucket_name = record["s3"]["bucket"]["name"]
        s3_key = record["s3"]["object"]["key"]
    except (KeyError, IndexError) as e:
        print(f"Error parsing S3 event structure: {str(e)}")
        return {"statusCode": 400, "body": "Malformed event structure."}

    parsed_meta = parse_s3_key(s3_key)
    if not parsed_meta["valid"]:
        return {"statusCode": 200, "body": json.dumps(parsed_meta["reason"])}

    project_id = parsed_meta["project_id"]
    category = parsed_meta["category"]
    final_key = parsed_meta["final_key"]

    if category == "images":
        try:
            process_and_route_image(bucket_name, src_key=s3_key, dest_key=final_key)
        except Exception as e:
            print(f"Error during image processing execution: {str(e)}")
            raise e
    else:
        try:
            print(f"Routing document asset to permanent storage: {final_key}")
            s3_client.copy_object(
                Bucket=bucket_name,
                CopySource={"Bucket": bucket_name, "Key": s3_key},
                Key=final_key,
            )
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        except Exception as e:
            print(f"Failed to copy standard document from raw workspace: {str(e)}")
            raise e

    try:
        quota_report = enforce_project_quota(bucket_name, final_key, project_id)
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "File pipeline processed successfully.",
                    "report": quota_report,
                }
            ),
        }
    except Exception as e:
        print(f"Error during validation limits calculation: {str(e)}")
        raise e
