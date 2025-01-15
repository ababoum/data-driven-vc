import { useState, useEffect } from 'react'
import { Container, Typography, Box, CssBaseline, ThemeProvider, createTheme, TextField, Alert, Button, CircularProgress, Paper } from '@mui/material'
import { analyzeDomain, getJobStatus } from './services/api'

const theme = createTheme({
  palette: {
    mode: 'light',
    background: {
      default: '#FAFAF0',
    },
    primary: {
      main: '#4A4A4A',
    },
  },
})

interface JobResult {
  domain: string;
  analyzed_at: string;
  metrics: {
    score: number;
    potential: string;
    market_size: string;
    company_age: string;
    market_position: string;
    recommendation: string;
  };
}

interface StepData {
  step: number;
  [key: string]: any;
}

function App() {
  const [searchValue, setSearchValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [analyzedDomain, setAnalyzedDomain] = useState<string | null>(null)
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<string | null>(null)
  const [jobResult, setJobResult] = useState<JobResult | null>(null)
  const [stepHistory, setStepHistory] = useState<StepData[]>([])

  useEffect(() => {
    let intervalId: number | null = null;

    const pollJob = async () => {
      if (!currentJobId) return;

      try {
        const response = await getJobStatus(currentJobId);
        setJobStatus(response.status);
        
        if (response.step_history) {
          setStepHistory(response.step_history);
        }

        if (response.completed) {
          if (response.result) {
            setJobResult(response.result);
          }
          if (intervalId) {
            window.clearInterval(intervalId);
          }
        }
      } catch (err) {
        setError('Failed to get job status');
        if (intervalId) {
          window.clearInterval(intervalId);
        }
      }
    };

    if (currentJobId) {
      intervalId = window.setInterval(pollJob, 1000); // Polling every second
      pollJob(); // Initial poll
    }

    return () => {
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [currentJobId]);

  const handleSubmit = async () => {
    try {
      setError(null);
      setJobResult(null);
      setJobStatus(null);
      setStepHistory([]);
      
      if (searchValue.trim()) {
        const response = await analyzeDomain(searchValue.trim());
        setCurrentJobId(response.job_id);
        setAnalyzedDomain(searchValue.trim());
      } else {
        setError('Please enter a domain name');
      }
    } catch (err) {
      setError('Failed to start analysis. Please try again.');
    }
  };

  const handleReset = () => {
    setSearchValue('');
    setError(null);
    setAnalyzedDomain(null);
    setCurrentJobId(null);
    setJobStatus(null);
    setJobResult(null);
    setStepHistory([]);
  };

  const renderStepData = (data: StepData) => {
    const stepTitles: { [key: number]: string } = {
      1: "Company Verification",
      2: "Market Analysis",
      3: "Financial Assessment",
      4: "Team Analysis",
      5: "Technology Stack",
      6: "Growth Metrics",
      7: "Risk Assessment",
      8: "Market Sentiment",
      9: "Competitive Analysis",
      10: "Final Scoring"
    };

    return (
      <Paper 
        key={data.step}
        sx={{ 
          p: 3, 
          mb: 2, 
          borderRadius: 2,
          opacity: 1,
          transform: 'translateY(0)',
          transition: 'opacity 0.5s ease, transform 0.5s ease',
          '&:new': {
            opacity: 0,
            transform: 'translateY(20px)',
          }
        }}
      >
        <Typography variant="h6" gutterBottom color="primary">
          Step {data.step}: {stepTitles[data.step]}
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {Object.entries(data)
            .filter(([key]) => key !== 'step')
            .map(([key, value]) => (
              <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography sx={{ textTransform: 'capitalize', color: 'text.secondary' }}>
                  {key.split('_').join(' ')}:
                </Typography>
                <Typography sx={{ fontWeight: 'bold' }}>{value}</Typography>
              </Box>
            ))}
        </Box>
      </Paper>
    );
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          display: 'flex',
          minHeight: '100vh',
          minWidth: '100vw',
          alignItems: analyzedDomain ? 'flex-start' : 'center',
          justifyContent: 'center',
          backgroundColor: '#FAFAF0',
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          margin: 0,
          padding: analyzedDomain ? '2rem 0' : 0,
          overflowY: 'auto'
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', position: 'relative' }}>
            {!analyzedDomain ? (
              <>
                <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: '#4A4A4A' }}>
                  Startech VC
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', maxWidth: '600px', margin: '0 auto' }}>
                  <TextField
                    fullWidth
                    variant="outlined"
                    placeholder="Type in the company [Domain Name] here..."
                    value={searchValue}
                    onChange={(e) => setSearchValue(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleSubmit();
                      }
                    }}
                    sx={{
                      backgroundColor: '#FFFFFF',
                      borderRadius: 1,
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: '#4A4A4A',
                        },
                        '&:hover fieldset': {
                          borderColor: '#4A4A4A',
                        },
                      },
                    }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleSubmit}
                    sx={{
                      height: '56px',
                      minWidth: '100px',
                      backgroundColor: '#4A4A4A',
                      '&:hover': {
                        backgroundColor: '#2A2A2A',
                      },
                    }}
                  >
                    Analyze
                  </Button>
                </Box>
              </>
            ) : (
              <>
                <Box sx={{ position: 'absolute', top: 0, right: 0 }}>
                  <Button
                    variant="outlined"
                    onClick={handleReset}
                    sx={{
                      borderColor: '#4A4A4A',
                      color: '#4A4A4A',
                      '&:hover': {
                        borderColor: '#2A2A2A',
                        backgroundColor: 'rgba(74, 74, 74, 0.1)',
                      },
                    }}
                  >
                    New Search
                  </Button>
                </Box>
                <Box sx={{ mt: 0, mb: 4 }}>
                  <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', color: '#4A4A4A' }}>
                    {analyzedDomain}
                  </Typography>
                </Box>
                {jobStatus && !jobResult && (
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, mb: 4 }}>
                    <CircularProgress />
                    <Typography variant="body1" color="text.secondary">
                      {jobStatus}
                    </Typography>
                  </Box>
                )}
                <Box sx={{ maxWidth: '800px', margin: '0 auto' }}>
                  {stepHistory.map((step) => renderStepData(step))}
                </Box>
                {jobResult && (
                  <Box sx={{ mt: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Typography variant="h5" component="h2">Final Analysis</Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 3 }}>
                      <Paper sx={{ p: 3, borderRadius: 2 }}>
                        <Typography variant="h4" gutterBottom>{jobResult.metrics.score}</Typography>
                        <Typography variant="subtitle1">Overall Score</Typography>
                      </Paper>
                      <Paper sx={{ p: 3, borderRadius: 2 }}>
                        <Typography variant="h4" gutterBottom>{jobResult.metrics.potential}</Typography>
                        <Typography variant="subtitle1">Potential</Typography>
                      </Paper>
                      <Paper sx={{ p: 3, borderRadius: 2 }}>
                        <Typography variant="h4" gutterBottom>{jobResult.metrics.market_size}</Typography>
                        <Typography variant="subtitle1">Market Size</Typography>
                      </Paper>
                      <Paper sx={{ p: 3, borderRadius: 2 }}>
                        <Typography variant="h4" gutterBottom>{jobResult.metrics.company_age}</Typography>
                        <Typography variant="subtitle1">Company Age</Typography>
                      </Paper>
                      <Paper sx={{ p: 3, borderRadius: 2 }}>
                        <Typography variant="h4" gutterBottom>{jobResult.metrics.market_position}</Typography>
                        <Typography variant="subtitle1">Market Position</Typography>
                      </Paper>
                      <Paper sx={{ p: 3, borderRadius: 2 }}>
                        <Typography variant="h4" gutterBottom>{jobResult.metrics.recommendation}</Typography>
                        <Typography variant="subtitle1">Recommendation</Typography>
                      </Paper>
                    </Box>
                  </Box>
                )}
              </>
            )}
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App