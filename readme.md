# Data Driven VC

![data driven vc](https://i.imgur.com/O8vZHPM.png)

> This project was built as part of the Data-Driven VC Hackathon organized by [Red River West](https://redriverwest.com) & [Bivwak! by BNP Paribas](https://bivwak.bnpparibas/)

A full-stack application for data-driven venture capital analysis.

## Project Structure
```
.
├── backend/              # FastAPI backend
│   └── main.py           # Main FastAPI application
|   └── requirements.txt  # Python dependencies
├── frontend/             # React frontend
└── docker-compose.yml    # Docker Compose configuration
```

## Setup Instructions

### Docker Setup

Simply run:
```bash
docker-compose up -d
```

### Manual setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend:
```bash
uvicorn main:app --reload
```
The API will be available at http://localhost:8000

4. Run the frontend:
```bash
npm run dev
```
