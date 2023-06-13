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
import csv
import json
import random
import pandas as pd
import numpy as np

current_directory = os.path.dirname(__file__)

application = FastAPI()
application.mount("/static", StaticFiles(directory=current_directory+"/static"), name="static")
application.mount("/css", StaticFiles(directory=current_directory+"/static/css"), name="css")
templates = Jinja2Templates(directory=current_directory+"/templates")

# Instantiate the gcs client
GOOGLE_STORAGE_CLIENT = storage.Client.from_service_account_json(current_directory + "/creds/lgbt-tv-data-f74cabb1c8e1.json")


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
    bucket_name = "lesbian-visibility-day"
    items = list_blobs_with_prefix(bucket_name, prefix="public-materials", delimiter=None)
    master_list = []
    for item in items:
        path_quoted = urllib.parse.quote(item, safe='/', encoding='utf-8')
        item_name_w_extension = item.split('/')[-1]
        item_name = item_name_w_extension.replace("."+item_name_w_extension.split('.')[-1], "")
        quoted = urllib.parse.quote(item_name_w_extension, safe='/', encoding='utf-8')
        url = f"https://storage.googleapis.com/lesbian-visibility-day/{path_quoted}"
        hash_id = hashlib.md5((item_name + url).encode('utf-8')).hexdigest()
        if item_name != '':
            master_list.append({"item_name": item_name, "url": url, "hash_id": hash_id})
        # print(master_list)
    return master_list


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


def split_into_columns_and_rows():
    photos = get_work()
    split_by_4 = len(photos) // 4
    # print("Length of group: " + str(split_by_4))
    split_photos = list(divide_chunks(photos, 4))
    return split_photos


def load_categories():
    filename = 'categories.csv'
    prompts = list()
    with open(filename, encoding = 'utf-8') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            prompts.append({"id": row['\ufeffcategory_id'], "category": row['category'], "prompt": row['prompt'], "short_prompt": row['short_prompt'], "points": int(row['points']), "answer": row['answer'], "image_url": row['image_url']})
    return prompts


def calculate_points(points_allocation):
    df = pd.DataFrame.from_records(points_allocation)
    pivot_df = pd.pivot_table(df, values='points', index=['name'], aggfunc=np.sum, fill_value=0)
    points_by_user = pivot_df.reset_index().to_json(orient='records')
    points_by_user = json.loads(points_by_user)
    list_of_images = ["https://api.time.com/wp-content/uploads/2017/09/edith-windsor-robert-maxwell.jpg",
                      "https://imageio.forbes.com/specials-images/imageserve/5ed560d07fe4060006bbce1e/0x0.jpg?format=jpg&crop=878,879,x422,y0,safe&height=416&width=416&fit=bounds",
                      "https://www.losangelesblade.com/content/files/2019/12/RISING_QUEER_STAR_DROPS_TRAILER_FOR_NEW_SERIES_LAB_08122019-e1575832879468.jpg",
                      "https://bookstr.com/wp-content/uploads/2022/03/HallSapphoTHUMBNAIL-NOTEXT-1200x1200-1-1024x1024.jpg",
                      "https://www.sexualdiversity.org/images/1/7-stripe-lesbian-flag.png"]
    for i in range(len(points_by_user)):
        points_by_user[i]['image_url'] = list_of_images[random.randint(0,4)]
    points_by_user.sort(key=lambda x: x['points'], reverse=True)
    # # testing
    # points_by_user = [
    #     {"name": "e.windsor", "image_url": "/images/edie.jpg","points": 10},
    #     {"name": "e.degeneres", "image_url": "/images/ellen.jpg","points": 12},
    #     {"name": "l.waithe", "image_url": "/images/lena.jpg","points": 15},
    #     {"name": "sappho", "image_url": "/images/sappho.jpg","points": 6},
    #     {"name": "s.ubaru", "image_url": "/images/subaru.png","points": 5}]
    # points_by_user.sort(key=lambda x: x['points'], reverse=True)
    return points_by_user

def get_leaderboard():
    master_list = get_work()
    prompts = load_categories()
    points_allocation = list()
    for row in master_list:
        item_name = row['item_name']
        # print(item_name)
        if item_name != '':
            split_up_name = item_name.split('_')
            # print(split_up_name)
            prompt_no = split_up_name[0]
            user_name = split_up_name[1]
            points = int([x['points'] for x in prompts if x['id'] == prompt_no][0])
            points_allocation.append({"name": user_name, "points": points, "prompt": prompt_no})
    points_calculated = calculate_points(points_allocation)
    return points_calculated

def order_items_by_prompt():
    master_list = get_work()
    prompts = load_categories()
    ordered_prompts = list()
    final_ordered = list()
    for row in master_list:
        item_name = row['item_name']
        if item_name != '':
            split_up_name = item_name.split('_')
            prompt_no = split_up_name[0]
            user_name = split_up_name[1]
            prompt = [x['category'] for x in prompts if x['id'] == prompt_no][0]
            dict_item = {"prompt": prompt_no, "image_url": row['url'], "submitted_by": user_name}
            ordered_prompts.append(dict_item)
    # ordered_prompts = [{"prompt": 1, "image_url": "thisisone.com", "submitted_by": "me"}, {"prompt": 1, "image_url": "thisistwo.com", "submitted_by": "me"}, {"prompt": 2, "image_url": "thisithree.com", "submitted_by": "me"}, {"prompt": 2, "image_url": "thisisfour.com", "submitted_by": "me"}, {"prompt": 3, "image_url": "thisisfive.com", "submitted_by": "me"}, {"prompt": 3, "image_url": "thisissix.com", "submitted_by": "me"}]
    from itertools import groupby
    ordered_prompts.sort(key=lambda x:int(x['prompt']))
    for k, v in groupby(ordered_prompts, key=lambda x: int(x['prompt'])):
        final_ordered.append((k, list(v)))
    print(final_ordered)
    final_ordered.sort()
    ultimate_ordered = list()
    for prompt_no, list_of_work in final_ordered:
        ultimate_ordered.append(({"no": prompt_no, "category": [x['short_prompt'] for x in prompts if str(x['id']) == str(prompt_no)][0]}, list_of_work))
    return ultimate_ordered


@application.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        # with open(current_directory  + "/photos/" + file.filename, "wb") as f:
        #     f.write(contents)
    except Exception:
        return {"message": "There was an error reading and uploading the file. Ensure it is a valid format ('png', 'jpg', 'jpeg', 'gif', 'webp')."}
    finally:
        file.file.close()
        try:
            if file.filename.split('.')[-1].lower() not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                raise Exception("invalid format")
            bucket = GOOGLE_STORAGE_CLIENT.get_bucket('lesbian-visibility-day')
            blob = bucket.blob("public-materials/" + file.filename)
            blob.upload_from_string(contents)
        except Exception as err:
            return {"message": "There was an error uploading the file to Google Storage: %s.  Ensure it is a valid format ('png', 'jpg', 'jpeg', 'gif', 'webp')."%(err)}
    return {"message": f"Successfully uploaded {file.filename}"}


@application.get("/", response_class=HTMLResponse)
def read_root(request: Request,
              current_work: list = Depends(get_work),
              split_photos: list = Depends(split_into_columns_and_rows),
              prompts: list = Depends(load_categories),
              leaderboard: list = Depends(get_leaderboard),
              split_photos_by_prompt: list = Depends(order_items_by_prompt)):
    return templates.TemplateResponse("index.html", {"request": request,
                                                     "current_work": current_work,
                                                     "split_photos": split_photos,
                                                     "prompts": prompts,
                                                     "leaderboard": leaderboard,
                                                     "split_photos_by_prompt": split_photos_by_prompt})

@application.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str, current_work: list = Depends(get_work)):
    for row in current_work:
        if row['hash_id'] == id:
            item = row
    return templates.TemplateResponse("item.html", {"request": request, "item": item})


@application.get("/uploadFile", response_class=HTMLResponse)
async def upload_file(request: Request,
                      prompts: list = Depends(load_categories)):
    return templates.TemplateResponse("upload.html", {"request": request, "prompts": prompts})


@application.get("/prompts", response_class=HTMLResponse)
def read_root(request: Request,
              prompts: list = Depends(load_categories)):
    return templates.TemplateResponse("prompts.html", {"request": request,
                                                     "prompts": prompts})


@application.get("/tips", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("tips.html", {"request": request})

