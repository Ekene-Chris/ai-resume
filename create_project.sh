#!/bin/bash

# Create the app directory and its subdirectories
mkdir -p app/api/routes
mkdir -p app/core
mkdir -p app/models
mkdir -p app/services
mkdir -p app/utils
mkdir -p app/data/roles
mkdir -p app/data/competency_matrix

# Create the tests directory
mkdir -p tests

# Create the scripts directory
mkdir -p scripts

# Create Python package init files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/routes/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py

# Create main application files
touch app/main.py
touch app/config.py

# Create API route files
touch app/api/routes/cv.py
touch app/api/routes/roles.py
touch app/api/routes/experience.py
touch app/api/dependencies.py

# Create core functionality files
touch app/core/security.py
touch app/core/azure_blob.py
touch app/core/azure_openai.py

# Create model files
touch app/models/cv.py
touch app/models/analysis.py
touch app/models/roles.py
touch app/models/experience.py

# Create service files
touch app/services/cv_analysis.py
touch app/services/feedback_generator.py
touch app/services/email_service.py

# Create utility files
touch app/utils/file_utils.py
touch app/utils/prompt_templates.py

# Create sample data files
touch app/data/roles/devops_engineer.json
touch app/data/roles/cloud_architect.json
touch app/data/experience_levels.json
touch app/data/competency_matrix/infrastructure.json
touch app/data/competency_matrix/cicd.json

# Create test files
touch tests/conftest.py
touch tests/test_cv_upload.py
touch tests/test_analysis.py

# Create script files
touch scripts/seed_data.py

# Create other base files
touch .env.example
touch .gitignore
touch pyproject.toml
touch requirements.txt
touch README.md
touch Dockerfile

echo "Project structure for ai-resume created successfully!"