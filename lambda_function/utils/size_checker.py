import os

import boto3

s3_client = boto3.client('s3')

SOFT_STORAGE_LIMIT = 1_073_741_824
HARD_STORAGE_LIMIT = int(SOFT_STORAGE_LIMIT * 1.10)

try:
    SOFT_STORAGE_LIMIT = int(os.environ.get("SOFT_STORAGE_LIMIT"))
    HARD_STORAGE_LIMIT = int(os.environ.get("HARD_STORAGE_LIMIT"))
except ValueError:
    print("Warning: Malformed environment configuration detected. Falling back to default thresholds.")


def calculate_project_total_size(bucket_name: str, project_id: str) -> int:
    total_size = 0
    categories = ['documents', 'images', 'misc']
    
    for category in categories:
        prefix = f"projects/{category}/{project_id}/"
        
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
        
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    total_size += obj['Size']
                    
    return total_size


def enforce_project_quota(bucket_name: str, s3_key: str, project_id: str) -> dict:
    total_size = calculate_project_total_size(bucket_name, project_id)
    
    if total_size > HARD_STORAGE_LIMIT:
        print(f"HARD LIMIT BREACH: Project {project_id} total is {total_size} bytes. Limit is {HARD_STORAGE_LIMIT} bytes.")
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"Action executed: Hard deleted '{s3_key}' (Exceeded max allocation).")
        return {"status": "hard_breach", "total_size_bytes": total_size, "action_taken": "file_deleted"}
        
    elif total_size > SOFT_STORAGE_LIMIT:
        print(f"WARNING: Project {project_id} has exceeded its soft quota allocation ({total_size} / {SOFT_STORAGE_LIMIT} bytes).")
        return {"status": "soft_warning", "total_size_bytes": total_size, "action_taken": "none"}
        
    return {"status": "safe", "total_size_bytes": total_size, "action_taken": "none"}