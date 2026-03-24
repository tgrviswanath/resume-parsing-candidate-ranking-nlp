import React, { useState, useRef } from "react";
import {
  Box, Button, CircularProgress, Alert, Typography, Paper,
  Chip, TextField, Divider, LinearProgress, IconButton, List,
  ListItem, ListItemText, Collapse,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { rankResumes } from "../services/resumeApi";

const SAMPLE_JD = `We are looking for a Senior Python Developer with experience in:
- Python, FastAPI or Django
- PostgreSQL, Redis
- Docker, Kubernetes, AWS
- Machine Learning, NLP, scikit-learn
- REST API design and microservices
- Git, CI/CD pipelines`;

const COLORS = ["#1976d2", "#388e3c", "#f57c00", "#7b1fa2", "#c62828"];

export default function RankPage() {
  const [files, setFiles] = useState([]);
  const [jd, setJd] = useState(SAMPLE_JD);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState({});
  const fileRef = useRef();

  const handleFiles = (newFiles) => {
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name));
      const added = Array.from(newFiles).filter((f) => !existing.has(f.name));
      return [...prev, ...added];
    });
  };

  const removeFile = (name) => setFiles((prev) => prev.filter((f) => f.name !== name));

  const handleRank = async () => {
    if (!files.length || !jd.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const fd = new FormData();
      files.forEach((f) => fd.append("files", f));
      fd.append("job_description", jd);
      const r = await rankResumes(fd);
      setResult(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Ranking failed.");
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (i) => setExpanded((prev) => ({ ...prev, [i]: !prev[i] }));

  const chartData = result?.candidates.map((c) => ({
    name: c.filename.replace(/\.[^.]+$/, ""),
    score: c.match_score,
  })) || [];

  const scoreColor = (s) => s >= 60 ? "success" : s >= 35 ? "warning" : "error";

  return (
    <Box>
      {/* File drop zone */}
      <Paper
        variant="outlined"
        onClick={() => fileRef.current.click()}
        onDrop={(e) => { e.preventDefault(); handleFiles(e.dataTransfer.files); }}
        onDragOver={(e) => e.preventDefault()}
        sx={{
          p: 2, mb: 2, textAlign: "center", cursor: "pointer", borderStyle: "dashed",
          "&:hover": { bgcolor: "action.hover" },
        }}
      >
        <input ref={fileRef} type="file" hidden multiple accept=".pdf,.docx,.doc,.txt"
          onChange={(e) => handleFiles(e.target.files)} />
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1 }}>
          <UploadFileIcon color="action" />
          <Typography color="text.secondary">
            Drag & drop or click — upload multiple resumes (PDF / DOCX / TXT)
          </Typography>
        </Box>
      </Paper>

      {/* File chips */}
      {files.length > 0 && (
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mb: 2 }}>
          {files.map((f) => (
            <Chip key={f.name} label={f.name} size="small" onDelete={() => removeFile(f.name)} />
          ))}
        </Box>
      )}

      {/* JD input */}
      <TextField
        fullWidth multiline rows={5}
        label="Job Description"
        value={jd}
        onChange={(e) => setJd(e.target.value)}
        sx={{ mb: 2 }}
        size="small"
      />

      <Button
        variant="contained" onClick={handleRank}
        disabled={!files.length || !jd.trim() || loading}
        startIcon={loading ? <CircularProgress size={16} color="inherit" /> : null}
        sx={{ mb: 2 }}
      >
        {loading ? "Ranking..." : `Rank ${files.length} Candidate${files.length !== 1 ? "s" : ""}`}
      </Button>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            {result.total} Candidates Ranked
          </Typography>

          {/* Score bar chart */}
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 30, left: 0 }}>
              <XAxis dataKey="name" angle={-20} textAnchor="end" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} unit="%" />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="score" radius={[4, 4, 0, 0]} label={{ position: "top", fontSize: 11 }}>
                {chartData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <Divider sx={{ my: 2 }} />

          {/* Ranked candidate cards */}
          {result.candidates.map((c, i) => (
            <Paper key={i} variant="outlined" sx={{ p: 2, mb: 1.5 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Chip label={`#${c.rank}`} size="small"
                    sx={{ bgcolor: COLORS[i % COLORS.length], color: "white", fontWeight: "bold" }} />
                  <Typography variant="subtitle2">{c.filename}</Typography>
                  {c.parsed.name && (
                    <Typography variant="body2" color="text.secondary">— {c.parsed.name}</Typography>
                  )}
                </Box>
                <Chip label={`${c.match_score}%`} color={scoreColor(c.match_score)} size="small" />
              </Box>

              <LinearProgress
                variant="determinate" value={c.match_score}
                color={scoreColor(c.match_score)}
                sx={{ height: 6, borderRadius: 3, mb: 1 }}
              />

              {/* Skills preview */}
              {c.parsed.skills.length > 0 && (
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mb: 1 }}>
                  {c.parsed.skills.slice(0, 8).map((s) => (
                    <Chip key={s} label={s} size="small" variant="outlined" />
                  ))}
                  {c.parsed.skills.length > 8 && (
                    <Chip label={`+${c.parsed.skills.length - 8} more`} size="small" />
                  )}
                </Box>
              )}

              {/* Expand for full details */}
              <Button size="small" onClick={() => toggleExpand(i)}
                endIcon={expanded[i] ? <ExpandLessIcon /> : <ExpandMoreIcon />}>
                {expanded[i] ? "Hide details" : "Show details"}
              </Button>
              <Collapse in={!!expanded[i]}>
                <Box sx={{ mt: 1, pl: 1 }}>
                  {c.parsed.email && <Typography variant="body2">📧 {c.parsed.email}</Typography>}
                  {c.parsed.phone && <Typography variant="body2">📞 {c.parsed.phone}</Typography>}
                  {c.parsed.linkedin && <Typography variant="body2">🔗 {c.parsed.linkedin}</Typography>}
                  {c.parsed.github && <Typography variant="body2">💻 {c.parsed.github}</Typography>}
                  {c.parsed.education.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" fontWeight="bold">Education</Typography>
                      {c.parsed.education.map((e, ei) => (
                        <Typography key={ei} variant="body2" color="text.secondary">• {e}</Typography>
                      ))}
                    </Box>
                  )}
                  {c.parsed.experience_dates.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" fontWeight="bold">Experience Dates</Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 0.5 }}>
                        {c.parsed.experience_dates.map((d, di) => (
                          <Chip key={di} label={d} size="small" variant="outlined" color="warning" />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              </Collapse>
            </Paper>
          ))}
        </Box>
      )}
    </Box>
  );
}
