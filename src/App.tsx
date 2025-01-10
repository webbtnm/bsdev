import { useNavigate, Outlet } from "react-router";
import Header from "@/components/Header";
import { useEffect } from "react";
import { useUser } from "../../client/src/hooks/use-user.ts";
import { Loader2 } from "lucide-react";

function App() {
    let navigate = useNavigate();

    const { user, isLoading } = useUser();

    useEffect(() => {
        if (!user && !isLoading) {
            navigate("/auth");
        }
    }, [user]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <>
            <Header />
            <Outlet />
        </>
    );
}

export default App;
