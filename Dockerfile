# 
FROM python:3.9

# 
COPY ./requirements.txt /app/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 
COPY ./app /app

#

EXPOSE 8080

# 
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
