import { useQuery } from "@tanstack/react-query";
import { queryClient } from "@/main.tsx";
import { useState } from "react";
import { Book, Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/button.tsx";
import CreateShelfDialog from "@/components/CreateShelfDialog.tsx";
import BrowseShelvesDialog from "@/components/BrowseShelvesDialog.tsx";
import { ShelfGrid } from "@/components/ShelfGrid";
import type { ShelvesResponse } from "@/types.ts";

export default function Shelves() {
    const user = queryClient.getQueryCache().find({ queryKey: ["user"] });
    const [createShelfOpen, setCreateShelfOpen] = useState(false);
    const [browseShelvesOpen, setBrowseShelvesOpen] = useState(false);
    const { data: response, isLoading } = useQuery<ShelvesResponse>({
        queryKey: ["shelves"],
        queryFn: async () => {
            const response = await fetch(
                "http://localhost:8000/api/user/shelves",
                {
                    credentials: "include",
                },
            );

            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    return null;
                }

                throw new Error(`${response.status}: ${await response.text()}`);
            }

            return response.json();
        },
        enabled: !!user,
    });

    const shelves = response?.shelves || [];

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <main className="container mx-auto py-8 px-4 min-h-screen bg-background">
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-2xl font-bold">Твои Полки</h2>
                <div className="flex gap-4">
                    <Button
                        variant="outline"
                        onClick={() => setBrowseShelvesOpen(true)}
                    >
                        <Search className="mr-2 h-4 w-4" />
                        Все Полки
                    </Button>
                    <Button onClick={() => setCreateShelfOpen(true)}>
                        <Book className="mr-2 h-4 w-4" />
                        Создать Полку
                    </Button>
                </div>
            </div>

            {shelves.length > 0 ? (
                <ShelfGrid shelves={shelves} />
            ) : (
                <div className="text-center py-12">
                    <p className="text-muted-foreground">
                        Полок пока нет. Создайте новую полку или посмотрите
                        полки других пользователей
                    </p>
                </div>
            )}

            <CreateShelfDialog
                open={createShelfOpen}
                onOpenChange={setCreateShelfOpen}
            />

            <BrowseShelvesDialog
                open={browseShelvesOpen}
                onOpenChange={setBrowseShelvesOpen}
            />
        </main>
    );
}
