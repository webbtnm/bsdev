import { Button } from "@/components/ui/button";
import { useUser } from "@/hooks/use-user";
import { Library, User } from "lucide-react";

export default function Header() {
    const { user, logout } = useUser();

    return (
        <header className="border-b">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <Button variant="ghost" className="flex items-center">
                        <Library className="h-6 w-6 text-primary mr-2" />
                        <span className="text-xl font-bold">букшéлф</span>
                    </Button>
                </div>

                <nav className="flex items-center space-x-4">
                    <Button variant="ghost" className="flex items-center">
                        <User className="h-4 w-4 mr-2" />
                        {user?.username}
                    </Button>
                    <Button variant="outline" onClick={() => logout()}>
                        Выйти
                    </Button>
                </nav>
            </div>
        </header>
    );
}
