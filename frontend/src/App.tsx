import { useState, useEffect } from 'react'
import { Container, Typography, Box, CssBaseline, ThemeProvider, createTheme, TextField, Alert, Button, CircularProgress, Paper, IconButton, useMediaQuery, Collapse, Tooltip } from '@mui/material'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import Brightness4Icon from '@mui/icons-material/Brightness4'
import Brightness7Icon from '@mui/icons-material/Brightness7'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { analyzeDomain, getJobStatus, summarizeStep } from './services/api'
import Markdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkMath from 'remark-math'
import remarkGfm from 'remark-gfm'
import 'katex/dist/katex.min.css'
import './styles/github-markdown.css'

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

function formatStepDataToMarkdown(data: StepData): string {
  const stepTitles: { [key: number]: string } = {
    1: "Competitors informations",
    2: "Founders",
    3: "Company Details",
    4: "Competitors",
    5: "Key People",
    6: "Market Analysis",
    7: "Financial Assessment",
    8: "Market Sentiment",
    9: "Competitive Analysis",
    10: "Final Scoring"
  };

  let markdown = `## ${stepTitles[data.step] || 'Analysis Step'}\n\n`;

  Object.entries(data)
    .filter(([key]) => !['step', '_performance'].includes(key))
    .forEach(([key, value]) => {
      const formattedKey = key.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ');

      if (Array.isArray(value)) {
        markdown += `### ${formattedKey}\n`;
        value.forEach((item: any) => {
          markdown += `- ${item}\n`;
        });
        markdown += '\n';
      } else {
        markdown += `### ${formattedKey}\n${value}\n\n`;
      }
    });

  return markdown;
}

function App() {
  const [mode, setMode] = useState<'light' | 'dark'>('dark');

  const stepTitles: { [key: number]: string } = {
    1: "Competitors informations",
    2: "Founders",
    3: "Company Details",
    4: "Competitors",
    5: "Key People",
    6: "Market Analysis",
    7: "Financial Assessment",
    8: "Market Sentiment",
    9: "Competitive Analysis",
    10: "Final Scoring"
  };

  const theme = createTheme({
    palette: {
      mode,
      background: {
        default: mode === 'dark' ? '#0d1117' : '#FAFAF0',
        paper: mode === 'dark' ? '#161b22' : '#ffffff',
      },
      primary: {
        main: mode === 'dark' ? '#58a6ff' : '#4A4A4A',
      },
      text: {
        primary: mode === 'dark' ? '#c9d1d9' : '#24292f',
        secondary: mode === 'dark' ? '#8b949e' : '#57606a',
      },
    },
  });

  const toggleColorMode = () => {
    setMode(prevMode => prevMode === 'light' ? 'dark' : 'light');
  };

  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  const [searchValue, setSearchValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [analyzedDomain, setAnalyzedDomain] = useState<string | null>(null)
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<string | null>(null)
  const [jobResult, setJobResult] = useState<JobResult | null>(null)
  const [stepHistory, setStepHistory] = useState<StepData[]>([])
  const [stepSummaries, setStepSummaries] = useState<{ [key: number]: string }>({});
  const [loadingSteps, setLoadingSteps] = useState<Set<number>>(new Set());
  const [expandedSteps, setExpandedSteps] = useState<Set<string | number>>(new Set());

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
      intervalId = window.setInterval(pollJob, 1000);
      pollJob();
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
      setStepSummaries({});
      setLoadingSteps(new Set());
      
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
    setStepSummaries({});
    setLoadingSteps(new Set());
  };

  const handleSummarize = async (stepData: StepData) => {
    try {
      setLoadingSteps(prev => new Set(prev).add(stepData.step));
      const response = await summarizeStep(stepData);
      setStepSummaries(prev => ({
        ...prev,
        [stepData.step]: response.summary
      }));
    } catch (err) {
      setError('Failed to generate summary');
    } finally {
      setLoadingSteps(prev => {
        const next = new Set(prev);
        next.delete(stepData.step);
        return next;
      });
    }
  };

  const toggleStep = (stepId: string | number) => {
    setExpandedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  const renderStepData = (data: StepData) => {
    const hasSummary = stepSummaries[data.step] !== undefined;
    const isLoading = loadingSteps.has(data.step);
    const isExpanded = expandedSteps.has(data.step);
    const isExplanationExpanded = expandedSteps.has(`${data.step}_explanation`);
    const stepTitle = stepTitles[data.step] || 'Analysis Step';

    const getBorderColor = (performance: number) => {
      switch(performance) {
        case 1:
          return mode === 'dark' ? '#238636' : '#2da44e';  // Green
        case -1:
          return mode === 'dark' ? '#da3633' : '#cf222e';  // Red
        case 0:
        default:
          return mode === 'dark' ? '#d29922' : '#d4a72c';  // Yellow
      }
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
          transition: 'all 0.5s ease',
          backgroundColor: theme.palette.background.paper,
          border: `3px solid ${data._performance !== undefined ? getBorderColor(data._performance) : (mode === 'dark' ? '#30363d' : '#e1e4e8')}`,
          '&:new': {
            opacity: 0,
            transform: 'translateY(20px)',
          },
          position: 'relative'
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: isExpanded ? 2 : 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton 
              onClick={() => toggleStep(data.step)}
              sx={{ 
                transform: isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)',
                transition: 'transform 0.3s ease',
              }}
            >
              <ExpandMoreIcon />
            </IconButton>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
              <Typography variant="h6" color="text.primary">
                {stepTitle}
              </Typography>
              {data.performance_comment && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {data.performance_comment}
                </Typography>
              )}
            </Box>
          </Box>
        </Box>

        <Collapse in={isExpanded}>
          <div className="markdown-body max-w-2xl w-full overflow-x-hidden">
            <style>{`
              .markdown-body {
                color: ${theme.palette.text.primary} !important;
                background-color: transparent !important;
                text-align: left !important;
              }
              .katex-display {
                display: block;
                overflow-x: auto;
                max-width: 100%;
                white-space: nowrap;
              }
            `}</style>

            <Markdown
              components={{
                ol: ({ ...props }) => <ol style={{ listStyle: "revert" }} {...props} />,
                ul: ({ ...props }) => <ul style={{ listStyle: "revert" }} {...props} />,
              }}
              remarkPlugins={[remarkMath, remarkGfm]}
              rehypePlugins={[rehypeKatex]}
            >
              {formatStepDataToMarkdown(data)}
            </Markdown>
          </div>

          {hasSummary && (
            <Box sx={{ 
              mt: 3, 
              p: 2, 
              borderRadius: 1,
              backgroundColor: mode === 'dark' ? 'rgba(88, 166, 255, 0.1)' : 'rgba(25, 118, 210, 0.08)',
            }}>
              <Typography variant="h6" gutterBottom color="primary">
                Summary
              </Typography>
              <Markdown
                remarkPlugins={[remarkMath, remarkGfm]}
                rehypePlugins={[rehypeKatex]}
              >
                {stepSummaries[data.step]}
              </Markdown>
            </Box>
          )}

          <Box sx={{ mt: 3 }}>
            <Button
              onClick={() => toggleStep(data.step + '_explanation')}
              sx={{
                color: theme.palette.text.secondary,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                '&:hover': {
                  backgroundColor: mode === 'dark' ? 'rgba(88, 166, 255, 0.1)' : 'rgba(25, 118, 210, 0.08)',
                }
              }}
            >
              <ExpandMoreIcon 
                sx={{ 
                  transform: isExplanationExpanded ? 'rotate(0deg)' : 'rotate(-90deg)',
                  transition: 'transform 0.3s ease',
                }}
              />
              <Typography variant="body2">
                How was this result calculated?
              </Typography>
            </Button>
            <Collapse in={isExplanationExpanded}>
              <Box sx={{ 
                mt: 1,
                p: 2,
                borderRadius: 1,
                backgroundColor: mode === 'dark' ? 'rgba(110,118,129,0.1)' : 'rgba(175,184,193,0.1)',
              }}>
                <Typography variant="body2" color="text.secondary">
                  {data.calculation_explanation || "This step's results are calculated by analyzing various data points and comparing them against industry standards and competitor benchmarks."}
                </Typography>
              </Box>
            </Collapse>

            {!hasSummary && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Tooltip title="Generate AI Summary" placement="left" arrow>
                  <IconButton 
                    onClick={() => handleSummarize(data)}
                    color="primary"
                    disabled={isLoading}
                    sx={{ 
                      backgroundColor: mode === 'dark' ? 'rgba(88, 166, 255, 0.1)' : 'rgba(25, 118, 210, 0.08)',
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        transform: 'scale(1.1)',
                        backgroundColor: mode === 'dark' ? 'rgba(88, 166, 255, 0.2)' : 'rgba(25, 118, 210, 0.16)',
                      }
                    }}
                  >
                    {isLoading ? <CircularProgress size={24} /> : <AutoFixHighIcon />}
                  </IconButton>
                </Tooltip>
              </Box>
            )}
          </Box>
        </Collapse>
      </Paper>
    );
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <style>{`
        .markdown-body {
          color: ${theme.palette.text.primary} !important;
          background-color: transparent !important;
        }
        .markdown-body h1,
        .markdown-body h2,
        .markdown-body h3,
        .markdown-body h4,
        .markdown-body h5,
        .markdown-body h6 {
          color: ${theme.palette.text.primary} !important;
          border-bottom-color: ${mode === 'dark' ? '#30363d' : '#e1e4e8'} !important;
        }
        .markdown-body a {
          color: ${mode === 'dark' ? '#58a6ff' : '#0969da'} !important;
        }
        .markdown-body hr {
          background-color: ${mode === 'dark' ? '#30363d' : '#e1e4e8'} !important;
        }
        .markdown-body blockquote {
          color: ${theme.palette.text.secondary} !important;
          border-left-color: ${mode === 'dark' ? '#30363d' : '#e1e4e8'} !important;
        }
        .markdown-body table tr {
          background-color: ${theme.palette.background.paper} !important;
          border-color: ${mode === 'dark' ? '#30363d' : '#e1e4e8'} !important;
        }
        .markdown-body table tr:nth-child(2n) {
          background-color: ${mode === 'dark' ? '#161b22' : '#f6f8fa'} !important;
        }
        .markdown-body table th,
        .markdown-body table td {
          border-color: ${mode === 'dark' ? '#30363d' : '#e1e4e8'} !important;
        }
        .markdown-body code {
          background-color: ${mode === 'dark' ? 'rgba(110,118,129,0.4)' : 'rgba(175,184,193,0.2)'} !important;
          color: ${theme.palette.text.primary} !important;
        }
        .markdown-body pre code {
          background-color: transparent !important;
        }
      `}</style>
      <Box
        sx={{
          display: 'flex',
          minHeight: '100vh',
          minWidth: '100vw',
          alignItems: analyzedDomain ? 'flex-start' : 'center',
          justifyContent: 'center',
          backgroundColor: theme.palette.background.default,
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
        <IconButton
          onClick={toggleColorMode}
          sx={{
            position: 'fixed',
            top: 16,
            left: 16,
            backgroundColor: theme.palette.background.paper,
            border: `1px solid ${mode === 'dark' ? '#30363d' : '#e1e4e8'}`,
            '&:hover': {
              backgroundColor: mode === 'dark' ? 'rgba(88, 166, 255, 0.1)' : 'rgba(74, 74, 74, 0.1)',
            },
          }}
        >
          {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
        </IconButton>

        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', position: 'relative' }}>
            {!analyzedDomain ? (
              <>
                <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: theme.palette.text.primary }}>
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
                      backgroundColor: theme.palette.background.paper,
                      borderRadius: 1,
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: theme.palette.text.primary,
                        },
                        '&:hover fieldset': {
                          borderColor: theme.palette.text.primary,
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
                      backgroundColor: theme.palette.primary.main,
                      '&:hover': {
                        backgroundColor: mode === 'dark' ? '#1f6feb' : '#2A2A2A',
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
                      borderColor: theme.palette.text.primary,
                      color: theme.palette.text.primary,
                      '&:hover': {
                        borderColor: theme.palette.text.secondary,
                        backgroundColor: mode === 'dark' ? 'rgba(88, 166, 255, 0.1)' : 'rgba(74, 74, 74, 0.1)',
                      },
                    }}
                  >
                    New Search
                  </Button>
                </Box>
                <Box sx={{ mt: 0, mb: 4 }}>
                  <Typography variant="h3" component="h1" sx={{ fontWeight: 'bold', color: theme.palette.text.primary }}>
                    {analyzedDomain}
                  </Typography>
                  {stepHistory.length > 0 && (
                    <Box sx={{ 
                      display: 'flex', 
                      gap: 0.75, 
                      mt: 2,
                      flexWrap: 'wrap',
                      justifyContent: 'center',
                      alignItems: 'center'
                    }}>
                      {stepHistory.map((step) => {
                        const getTooltipContent = (step: StepData) => {
                          const title = `${stepTitles[step.step]}\n`;
                          switch(step.step) {
                            case 1:
                              return title + `${step.performance_comment}\nCompetitors Found: ${step.competitors ? 'Yes' : 'No'}`;
                            case 2:
                              return title + `${step.performance_comment}\nMarket Size: ${step.market_size}\nGrowth: ${step.market_growth}`;
                            case 3:
                              return title + `${step.performance_comment}\nMarket Position: ${step.market_position || 'N/A'}`;
                            case 7:
                              return title + `Revenue: ${step.revenue_range}\nBurn Rate: ${step.burn_rate}`;
                            case 8:
                              return title + `Team Size: ${step.team_size}\nTech Ratio: ${step.technical_ratio}`;
                            case 9:
                              return title + `Stack: ${step.infrastructure}\nLanguages: ${step.main_languages}`;
                            default:
                              return title;
                          }
                        };

                        const getBadgeColor = (performance: number) => {
                          switch(performance) {
                            case 1:
                              return mode === 'dark' ? '#238636' : '#2da44e';  // Green
                            case -1:
                              return mode === 'dark' ? '#da3633' : '#cf222e';  // Red
                            case 0:
                            default:
                              return mode === 'dark' ? '#d29922' : '#d4a72c';  // Yellow
                          }
                        };

                        // Only show important steps in overview
                        if (![1, 2, 3, 7, 8, 9].includes(step.step)) return null;

                        return (
                          <Tooltip 
                            key={step.step}
                            title={getTooltipContent(step)}
                            arrow
                            placement="bottom"
                          >
                            <Box sx={{ 
                              width: '12px',
                              height: '12px',
                              borderRadius: '2px',
                              backgroundColor: step._performance !== undefined ? getBadgeColor(step._performance) : (mode === 'dark' ? '#30363d' : '#e1e4e8'),
                              cursor: 'pointer',
                              transition: 'transform 0.2s ease',
                              '&:hover': {
                                transform: 'scale(1.2)',
                              }
                            }} />
                          </Tooltip>
                        );
                      })}
                    </Box>
                  )}
                </Box>
                {jobStatus && !jobResult && (
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, mb: 4 }}>
                    <CircularProgress />
                    <Typography variant="body1" color="text.secondary">
                      {jobStatus}
                    </Typography>
                  </Box>
                )}
                <Box sx={{ maxWidth: '800px', margin: '0 auto', textAlign: 'left' }}>
                  {stepHistory.map((step) => renderStepData(step))}
                </Box>
                {jobResult && (
                  <Box sx={{ mt: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Typography variant="h5" component="h2" color="text.primary">Final Analysis</Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 3 }}>
                      {Object.entries(jobResult.metrics).map(([key, value]) => (
                        <Paper 
                          key={key} 
                          sx={{ 
                            p: 3, 
                            borderRadius: 2,
                            backgroundColor: theme.palette.background.paper,
                            border: `1px solid ${mode === 'dark' ? '#30363d' : '#e1e4e8'}`,
                          }}
                        >
                          <Typography variant="h4" gutterBottom color="text.primary">{value}</Typography>
                          <Typography variant="subtitle1" color="text.secondary">
                            {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                          </Typography>
                        </Paper>
                      ))}
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