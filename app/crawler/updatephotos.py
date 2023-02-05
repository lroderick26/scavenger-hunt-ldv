import os
import requests
# Imports the Google Cloud client library
from google.cloud import storage

# Instantiates a client
storage_client = storage.Client.from_service_account_json("/creds/lgbt-tv-data-f74cabb1c8e1.json")

# The name for the top level bucket
bucket_name = "public-materials"

def list_blobs_with_prefix(bucket_name, prefix, delimiter=None):
    """Lists all the blobs in the bucket that begin with the prefix.
    This can be used to list all blobs in a "folder", e.g. "public/".
    The delimiter argument can be used to restrict the results to only the
    "files" in the given "folder". Without the delimiter, the entire tree under
    the prefix is returned. For example, given these blobs:
        a/1.txt
        a/b/2.txt
    If you specify prefix ='a/', without a delimiter, you'll get back:
        a/1.txt
        a/b/2.txt
    However, if you specify prefix='a/' and delimiter='/', you'll get back
    only the file directly under 'a/':
        a/1.txt
    As part of the response, you'll also get back a blobs.prefixes entity
    that lists the "subfolders" under `a/`:
        a/b/
    """
    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix, delimiter=delimiter)
    print("Blobs:")
    items = []
    for blob in blobs:
        items.append(blob.name)
    if delimiter:
        print("Prefixes:")
        for prefix in blobs.prefixes:
            print(prefix)
    return items


items = list_blobs_with_prefix(bucket_name, delimiter=None)

