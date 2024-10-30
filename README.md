# Wilson AI API

## Overview

This repository contains the code for Wilson AI API, a FastAPI / React application where you can intelligently interact with your medical data. 

This is a development project/POC. The application would need a real data source of medical professionals stored in Postgres/MongoDB
to fully work, but you can input toy examples and see how it is able to correctly recommend 
Medical practitioners you can follow up with based on your data.

1. **Backend**: A FastAPI application located in the `src/backend` directory.
2. **Frontend**: A React application located in the `src/frontend` directory.

## Prerequisites

- Python 3.10
- Node.js (v18.7.0)
- Docker (optional, for containerized deployment)
- MongoDB
- Redis
- ChromaDB

## Getting Started

### Backend

#### Setting Up the Backend

1. **Navigate to the backend directory**:

    ```sh
    cd src/backend
    ```

2. **Create a virtual environment**:

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:

    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:

    Create a `.env` file in the `src/backend` directory and add the following environment variables:

    ```env
    ENV=DEV
    CONFIG_PATH=src/backend/app/utils/config.yaml
    LOGGING_CONFIG_PATH=src/backend/app/utils/logging_config.yaml
    MONGODB_URL=mongodb://localhost:27017
    REDIS_URL=redis://localhost:6379
    CHROMADB_URL=http://localhost:8000
    CHROMADB_PATH=/chroma/chroma
    OPENAI_API_KEY=your_openai_api_key
    HUGGINGFACE_API_KEY=your_huggingface_api_key
    GOOGLE_MAPS_API_KEY=your_google_maps_api_key
    AWS_ACCESS_KEY_ID=your_aws_access_key_id
    AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
    AWS_REGION=your_aws_region
    S3_BUCKET_NAME=your_s3_bucket_name
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=your_postgres_db
    POSTGRES_USER=your_postgres_user
    POSTGRES_PASSWORD=your_postgres_password
    ```

5. **Run the backend server**:
    Ensure that you have the Redis, Postgres, and Mongodb daemons running! 
    You can then start the FastAPI server with: 
    ```sh
    uvicorn app.main:app --reload
    ```

### Frontend

#### Setting Up the Frontend

1. **Navigate to the frontend directory**:

    ```sh
    cd src/frontend
    ```

2. **Install the dependencies**:

    ```sh
    npm install
    ```

3. **Run the frontend development server**:

    ```sh
    npm run dev
    ```

### Docker

#### Running with Docker

1. **Build and run the Docker containers**:

    ```sh
    docker-compose up --build
    ```

## Linting and Formatting

### Backend

1. **Lint the backend code**:

    ```sh
    cd src/backend
    flake8
    ```

2. **Format the backend code**:

    ```sh
    black .
    ```

### Frontend

1. **Lint the frontend code**:

    ```sh
    cd src/frontend
    npx eslint .
    ```

2. **Format the frontend code**:

    ```sh
    npm run format
    ```

## Deployment

### GitHub Actions

The project uses GitHub Actions for continuous integration and deployment. The workflow is defined in `.github/workflows/deployment.yaml`.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.