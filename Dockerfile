# 
FROM python:3.9

# 
COPY ./requirements.txt /app/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 
COPY ./ /

#

EXPOSE 8080

# 
CMD ["uvicorn", "main:application", "--host", "0.0.0.0", "--port", "8080"]
#CMD ["gunicorn", "main:application", "--workers", "4",  "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]