import { StrictMode } from "react";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";
import "./index.css";
import App from "./App.tsx";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Auth from "@/routes/Auth.tsx";
import Shelves from "@/routes/Shelves.tsx";
import Profile from "@/routes/Profile.tsx";
import Shelf from "@/routes/Shelf.tsx";

export const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
    <QueryClientProvider client={queryClient}>
        <ReactQueryDevtools />
        <StrictMode>
            <BrowserRouter>
                <Routes>
                    <Route element={<App />}>
                        <Route index path="/" element={<Shelves />} />
                        <Route path="profile" element={<Profile />} />
                        <Route path="shelf" element={<Shelf />} />
                    </Route>
                    <Route path="auth" element={<Auth />} />
                </Routes>
            </BrowserRouter>
            ,
        </StrictMode>
    </QueryClientProvider>,
);
