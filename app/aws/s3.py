from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request, UploadFile
from types_aiobotocore_s3 import S3Client

from app.core.exceptions import DataIntegrityError
from app.core.settings import settings


async def get_s3_client(request: Request) -> S3Client:
    return request.app.state.s3_client


S3_CLIENT = Annotated[S3Client, Depends(get_s3_client)]


def s3_key_generator(
    project_id: str,
    document_id: str,
    file_extension: str,
    base_folder: str = "projects",
) -> str:
    extension = file_extension.lower()
    if extension in settings.ALLOWED_IMAGE_EXTENSIONS:
        sub_folder = "images"
        extension = ".jpg"
    elif extension in settings.ALLOWED_DOCUMENT_EXTENSIONS:
        sub_folder = "documents"
    else:
        raise DataIntegrityError("Invalid file extension.")

    return f"{base_folder}/{sub_folder}/{project_id}/{document_id}{extension}"


async def upload_file_s3(
    file: UploadFile,
    s3_bucket: str,
    s3_key: str,
    content_type: str,
    project_id: UUID,
    document_id: UUID,
    s3_client: S3Client,
) -> None:
    await s3_client.upload_fileobj(
        file.file,
        s3_bucket,
        s3_key,
        ExtraArgs={
            "ContentType": content_type,
            "Metadata": {
                "project_id": str(project_id),
                "document_id": str(document_id),
            },
        },
    )


async def get_download_url_s3(
    s3_key: str, s3_client: S3Client, expiration: int = 3600
) -> str:
    url = await s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": s3_key},
        ExpiresIn=expiration,
    )
    return url


async def delete_file_s3(s3_bucket: str, s3_key: str, s3_client: S3Client):
    await s3_client.delete_object(Bucket=s3_bucket, Key=s3_key)


async def delete_folder_s3(
    bucket_name: str, folder_prefix: str, s3_client: S3Client
) -> None:
    paginator = s3_client.get_paginator("list_objects_v2")

    async for page in paginator.paginate(Bucket=bucket_name, Prefix=folder_prefix):
        if "Contents" in page:
            objects_to_delete = [{"Key": obj["Key"]} for obj in page["Contents"]]

            await s3_client.delete_objects(
                Bucket=bucket_name, Delete={"Objects": objects_to_delete}
            )
