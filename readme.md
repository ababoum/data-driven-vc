# Data Driven VC

![alt text](https://i.imgur.com/O8vZHPM.png)

> This project was built as part of the Data-Driven VC Hackathon organized by [Red River West](https://redriverwest.com) & [Bivwak! by BNP Paribas](https://bivwak.bnpparibas/)

A full-stack application for data-driven venture capital analysis.

## Project Structure
```
.
├── backend/           # FastAPI backend
│   └── main.py       # Main FastAPI application
├── frontend/         # React frontend (to be created)
└── requirements.txt  # Python dependencies
```

## Setup Instructions

### Backend Setup
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
uvicorn backend.main:app --reload
```
The API will be available at http://localhost:8000

### Frontend Setup
Run:
```bash
npm run dev
```
