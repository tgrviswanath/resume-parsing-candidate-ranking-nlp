import React from "react";
import { AppBar, Toolbar, Typography } from "@mui/material";
import WorkIcon from "@mui/icons-material/Work";

export default function Header() {
  return (
    <AppBar position="static" color="primary">
      <Toolbar>
        <WorkIcon sx={{ mr: 1 }} />
        <Typography variant="h6" fontWeight="bold">
          Resume Parsing & Candidate Ranking
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
