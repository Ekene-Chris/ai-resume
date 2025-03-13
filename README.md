# AI Resume Analyzer

An AI-powered resume analyzer for tech professionals, leveraging Azure OpenAI to provide targeted feedback on resumes for DevOps, Cloud, and other technical roles.

## Features

- Resume upload and processing (PDF, DOCX)
- AI-powered resume analysis against role-specific requirements
- Targeted feedback for technical roles
- Skills gap analysis based on the Global DevOps Competency Matrix
- Keyword optimization suggestions

## Tech Stack

- **Backend**: FastAPI (Python)
- **Storage**: Azure Blob Storage
- **AI**: Azure OpenAI
- **Frontend**: React (separate repository)

## Setup

### Prerequisites

- Python 3.8+
- Azure Blob Storage account
- Azure OpenAI account
- Azure OpenAI deployment

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/ai-resume.git
   cd ai-resume
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file from the example:

   ```bash
   cp .env.example .env
   ```

5. Fill in your Azure credentials in the `.env` file

### Running the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000, and the API documentation at http://localhost:8000/docs.

## API Endpoints

- `POST /api/cv/upload`: Upload a resume for analysis
- `GET /api/cv/{analysis_id}/status`: Check the status of an analysis
- `GET /api/cv/{analysis_id}`: Get analysis results

## Project Structure

```
ai-resume/
├── app/                      # Main application package
│   ├── api/                  # API endpoints
│   ├── core/                 # Core functionality
│   ├── models/               # Pydantic models
│   ├── services/             # Business logic
│   ├── utils/                # Utility functions
│   └── data/                 # Static data and resources
├── tests/                    # Test suite
├── .env.example              # Example environment variables
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```

## Development

### Adding New Roles

To add support for a new role, create a JSON file in `app/data/roles/` following the existing format.

### Running Tests

```bash
pytest
```

## License

[MIT License](LICENSE)

## Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com).
