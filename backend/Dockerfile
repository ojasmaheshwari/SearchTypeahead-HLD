FROM python:3.12-slim

WORKDIR /code

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app /code/app
COPY frontend /code/frontend
COPY scripts /code/scripts
COPY dataset.csv /code/dataset.csv
COPY backend/tests /code/tests
COPY backend/pytest.ini /code/pytest.ini

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
