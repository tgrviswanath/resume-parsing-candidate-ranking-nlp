import React, { useState } from "react";
import { Container, Box, Tabs, Tab } from "@mui/material";
import Header from "./components/Header";
import ParsePage from "./pages/ParsePage";
import RankPage from "./pages/RankPage";

export default function App() {
  const [tab, setTab] = useState(0);
  return (
    <>
      <Header />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
          <Tab label="Parse Resume" />
          <Tab label="Rank Candidates" />
        </Tabs>
        <Box>{tab === 0 ? <ParsePage /> : <RankPage />}</Box>
      </Container>
    </>
  );
}
