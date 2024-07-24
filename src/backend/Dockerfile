FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN echo "Directory structure:" && ls -R
RUN find / -name main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]