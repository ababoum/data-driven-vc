# Nontech VC - Data-Driven Investment Analysis Platform

A modern web application that performs comprehensive analysis of tech companies using multiple data sources to provide investment insights.

## Features

- **Real-time Company Analysis**: Analyze any tech company using just their domain name
- **Multi-factor Assessment**: 14-step analysis covering:
  - Competitor Analysis
  - GitHub Repository Analysis
  - Code Quality Assessment
  - Founder Background Analysis
  - Key People Assessment
  - Market Analysis
  - Financial Assessment
  - Team Composition
  - Technology Stack
  - Growth Metrics
  - Risk Assessment
  - Market Sentiment
  - Competitive Position
  - Final Scoring

- **Interactive UI**:
  - Dark/Light mode support
  - Real-time progress tracking
  - Expandable detailed analysis for each step
  - AI-powered explanations
  - Visual performance indicators
  - Markdown support for rich text formatting

## Tech Stack

### Frontend
- React with TypeScript
- Material-UI (MUI) for components
- React-Markdown for content rendering
- KaTeX for mathematical formulas

### Backend
- FastAPI (Python)
- Async processing for real-time updates
- Integration with multiple data providers:
  - Harmonic.ai for company data
  - GitHub API for repository analysis
  - OpenAI API for intelligent summaries

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/data-driven-vc.git
cd data-driven-vc
```

2. Set up environment variables:
Create a `.env` file in the root directory with:
```env
HARMONIC_API_KEY=your_harmonic_api_key
OPENAI_API_KEY=your_openai_api_key
```

3. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
```

5. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

6. Start the frontend development server:
```bash
cd frontend
npm run dev
```

## Usage

1. Open the application in your browser
2. Enter a company's domain name in the search field
3. Click "Analyze" to start the assessment
4. Watch as each analysis step completes in real-time
5. Expand any step to view detailed information
6. Use the "Explain this to me" button for AI-generated summaries
7. Toggle dark/light mode as needed

## API Endpoints

- `POST /analyze-domain`: Start a new analysis
- `GET /job/{job_id}`: Get analysis status and results
- `POST /summarize-step`: Get AI explanation for a step

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Harmonic.ai for company data
- OpenAI for AI capabilities
- Material-UI for the component library
- All other open-source libraries used in this project
