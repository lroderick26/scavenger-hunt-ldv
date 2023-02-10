from typing import Optional
from fastapi import FastAPI, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


import os
import requests
from google.cloud import storage
import urllib.parse
import hashlib
import base64
from email.mime.text import MIMEText

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/css", StaticFiles(directory="app/static/css"), name="css")
templates = Jinja2Templates(directory="app/templates")

# Instantiate the gcs client
# GOOGLE_STORAGE_CLIENT = storage.Client.from_service_account_json("/app/creds/lgbt-tv-data-f74cabb1c8e1.json")
# GOOGLE_STORAGE_CLIENT = storage.Client.from_service_account_json("/Users/l.roderick/Documents/GitHub/lvd/app/creds/lgbt-tv-data-cc289e1b9b34.json")
GOOGLE_STORAGE_CLIENT = storage.Client.from_service_account_json("/app/creds/lgbt-tv-data-cc289e1b9b34.json")

def list_blobs_with_prefix(bucket_name, prefix=None, delimiter=None):
    """Lists all the blobs in the bucket that begin with the prefix. """
    # Note: Client.list_blobs requires at least package version 1.17.0.
    # blobs = GOOGLE_STORAGE_CLIENT.list_blobs(bucket_name, prefix=prefix, delimiter=delimiter)
    blobs = GOOGLE_STORAGE_CLIENT.list_blobs(bucket_name, delimiter=delimiter)
    items = []
    for blob in blobs:
        items.append(blob.name)
    if delimiter:
        print("Prefixes:")
        for prefix in blobs.prefixes:
            print(prefix)
    return items


def get_work():
    bucket_name = "public-materials"
    items = list_blobs_with_prefix(bucket_name, delimiter=None)
    master_list = []
    for item in items:
        path_quoted = urllib.parse.quote(item, safe='/', encoding='utf-8')
        item_name_w_extension = item.split('/')[-1]
        item_name = item_name_w_extension.split('.')[0]
        quoted = urllib.parse.quote(item_name_w_extension, safe='/', encoding='utf-8')
        url = f"https://storage.googleapis.com/public-materials/{path_quoted}"
        hash_id = hashlib.md5((item_name + url).encode('utf-8')).hexdigest()
        master_list.append({"item_name": item_name, "url": url, "hash_id": hash_id})
    return master_list

def split_into_columns_and_rows():
    photos = get_work()
    split_by_4 = len(photos) // 4


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        with open("uploaded_" + file.filename, "wb") as f:
            f.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Successfuly uploaded {file.filename}"}


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request,  current_work: list = Depends(get_work)):
    return templates.TemplateResponse("index.html", {"request": request, "current_work": current_work})

@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str, current_work: list = Depends(get_work)):
    for row in current_work:
        if row['hash_id'] == id:
            item = row
    return templates.TemplateResponse("item.html", {"request": request, "item": item})
