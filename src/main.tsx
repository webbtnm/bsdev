import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from "react-router";
import './index.css'
import App from './App.tsx'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Auth from '@/routes/Auth.tsx';
const queryClient = new QueryClient()

createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <StrictMode>
      <BrowserRouter>
        <Routes>
          <Route path="/" index element={<App/>}/>
          <Route path="/auth" element={<Auth/>}/>
        </Routes>
      </BrowserRouter>,
    </StrictMode>
  </QueryClientProvider>
)
