import React, { useState, useRef } from "react";
import {
  Box, Button, CircularProgress, Alert, Typography, Paper,
  Chip, Divider, Grid,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import { parseResume } from "../services/resumeApi";

const FIELD_COLOR = {
  skills: "primary",
  education: "success",
  experience_dates: "warning",
};

export default function ParsePage() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef();

  const handleFile = async (file) => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await parseResume(fd);
      setResult(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Parse failed.");
    } finally {
      setLoading(false);
    }
  };

  const p = result?.parsed;

  return (
    <Box>
      {/* Drop zone */}
      <Paper
        variant="outlined"
        onClick={() => fileRef.current.click()}
        onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); }}
        onDragOver={(e) => e.preventDefault()}
        sx={{
          p: 3, mb: 3, textAlign: "center", cursor: "pointer", borderStyle: "dashed",
          "&:hover": { bgcolor: "action.hover" },
        }}
      >
        <input ref={fileRef} type="file" hidden accept=".pdf,.docx,.doc,.txt"
          onChange={(e) => handleFile(e.target.files[0])} />
        {loading
          ? <CircularProgress size={24} />
          : <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1 }}>
              <UploadFileIcon color="action" />
              <Typography color="text.secondary">
                Drag & drop or click — PDF / DOCX / TXT
              </Typography>
            </Box>
        }
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {p && (
        <Paper variant="outlined" sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            {result.filename}
          </Typography>
          <Divider sx={{ mb: 2 }} />

          <Grid container spacing={2}>
            {/* Contact info */}
            {[
              { label: "Name", value: p.name },
              { label: "Email", value: p.email },
              { label: "Phone", value: p.phone },
              { label: "LinkedIn", value: p.linkedin },
              { label: "GitHub", value: p.github },
            ].map(({ label, value }) => value && (
              <Grid item xs={12} sm={6} key={label}>
                <Typography variant="caption" color="text.secondary">{label}</Typography>
                <Typography variant="body2" fontWeight="medium">{value}</Typography>
              </Grid>
            ))}
          </Grid>

          <Divider sx={{ my: 2 }} />

          {/* Skills */}
          {p.skills.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>Skills ({p.skills.length})</Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                {p.skills.map((s) => (
                  <Chip key={s} label={s} size="small" color={FIELD_COLOR.skills} variant="outlined" />
                ))}
              </Box>
            </Box>
          )}

          {/* Education */}
          {p.education.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>Education</Typography>
              {p.education.map((e, i) => (
                <Typography key={i} variant="body2" color="text.secondary">• {e}</Typography>
              ))}
            </Box>
          )}

          {/* Experience dates */}
          {p.experience_dates.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>Experience Dates</Typography>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                {p.experience_dates.map((d, i) => (
                  <Chip key={i} label={d} size="small" color={FIELD_COLOR.experience_dates} variant="outlined" />
                ))}
              </Box>
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
}
