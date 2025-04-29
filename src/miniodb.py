from minio import Minio
import os

user_name = os.environ.get("user_name")
password = os.environ.get("password")

if __name__ == "__main__":
    client = Minio(
        "127.0.0.1:9000", access_key=user_name, secret_key=password, secure=False
    )
    src_file = "../test.txt"
    bucket_name = "test-bucket-name"
    dest_name = "The_uploaded_file_name.txt"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print("Bucket name was not found, so it was created")
    else:
        print("The bucket named", bucket_name, "already exists!")

    client.fput_object(bucket_name, dest_name, src_file)
    print("Successfully uploaded", src_file, "to bucket", bucket_name, "as", dest_name)
