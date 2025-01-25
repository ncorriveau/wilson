# MedTrack AI

## Overview

An application enabling users to upload, organize, and analyze medical summaries and medication records, with AI-driven insights for actionable next steps in healthcare. Built with React, TypeScript, FastAPI, Redis, MongoDB, Postgres, and OpenAI API.

This is a development project/POC. You will need to set up the schemas in the postgres instance / and the document collection in MongoDB and 
fill these with sample values. To simplify this, there is CREATE_QUERIES list in src/backend/app/db/relational_db.py. 

Please reach out if you would like to get examples of potential data to fill in. 

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

This project is licensed under the MIT License.
