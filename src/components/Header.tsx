import { Button } from "@/components/ui/button";
import { useUser } from "@/hooks/use-user";
import { Library, User } from "lucide-react";
import { NavLink } from "react-router";
import { queryClient } from "@/main.tsx";
import type { UserDTO } from "@/types.ts";

export default function Header() {
    const user: UserDTO = queryClient.getQueryData(["user"])!;
    const { logout } = useUser();

    return (
        <header className="border-b">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <NavLink to="/">
                        <Button variant="ghost" className="flex items-center">
                            <Library className="h-6 w-6 text-primary mr-2" />
                            <span className="text-xl font-bold">букшéлф</span>
                        </Button>
                    </NavLink>
                </div>

                <nav className="flex items-center space-x-4">
                    <NavLink to="/profile">
                        <Button variant="ghost" className="flex items-center">
                            <User className="h-4 w-4 mr-2" />
                            {user?.username}
                        </Button>
                    </NavLink>
                    <Button variant="outline" onClick={() => logout()}>
                        Выйти
                    </Button>
                </nav>
            </div>
        </header>
    );
}
