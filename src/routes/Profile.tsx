import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Book as BookIcon, Settings, Loader2 } from "lucide-react";
import BookCard from "@/components/BookCard";
import AddBookDialog from "@/components/AddBookDialog";
import { queryClient } from "@/main.tsx";
import { Book } from "@/types.ts";
import type { UserDTO } from "@/types.ts";

export default function Profile() {
    const user: UserDTO = queryClient.getQueryData(["user"])!;

    const { toast } = useToast();
    const [isEditing, setIsEditing] = useState(false);
    const [editedContact, setEditedContact] = useState(
        user?.telegram_contact || "",
    );
    const [isAddBookDialogOpen, setIsAddBookDialogOpen] = useState(false);

    const {
        data: books = [],
        isLoading: isLoadingBooks,
        error: booksError,
    } = useQuery<Book[]>({
        queryKey: ["/api/books"],
        enabled: !!user,
    });

    const updateProfileMutation = useMutation({
        mutationFn: async (data: { telegramContact: string }) => {
            const response = await fetch("/api/user/profile", {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
                credentials: "include",
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["/api/user"] });
            toast({
                title: "Success",
                description: "Profile updated successfully",
            });
            setIsEditing(false);
        },
        onError: (error: Error) => {
            toast({
                title: "Error",
                description: error.message,
                variant: "destructive",
            });
        },
    });

    const handleUpdateProfile = async () => {
        await updateProfileMutation.mutateAsync({
            telegramContact: editedContact,
        });
    };

    if (booksError) {
        toast({
            title: "Error",
            description: "Failed to load books",
            variant: "destructive",
        });
    }

    return (
        <div className="min-h-screen bg-background">
            <div className="container mx-auto px-4 py-8">
                <Card className="mb-8">
                    <CardHeader>
                        <div className="flex justify-between items-center">
                            <CardTitle className="text-2xl">
                                Profile Information
                            </CardTitle>
                            <Button
                                variant="outline"
                                size="icon"
                                onClick={() => setIsEditing(!isEditing)}
                            >
                                <Settings className="h-4 w-4" />
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div>
                                <Label>Username</Label>
                                <p className="text-muted-foreground">
                                    {user?.username}
                                </p>
                            </div>
                            <div>
                                <Label htmlFor="telegramContact">
                                    Telegram Contact
                                </Label>
                                {isEditing ? (
                                    <div className="flex gap-4 mt-2">
                                        <Input
                                            id="telegramContact"
                                            value={editedContact}
                                            onChange={(e) =>
                                                setEditedContact(e.target.value)
                                            }
                                            placeholder="@username"
                                        />
                                        <Button onClick={handleUpdateProfile}>
                                            Save
                                        </Button>
                                    </div>
                                ) : (
                                    <p className="text-muted-foreground">
                                        {user?.telegram_contact ||
                                            "Not provided"}
                                    </p>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <div className="flex justify-between items-center mb-8">
                    <h2 className="text-2xl font-bold">My Books</h2>
                    <Button onClick={() => setIsAddBookDialogOpen(true)}>
                        <BookIcon className="mr-2 h-4 w-4" />
                        Add Book
                    </Button>
                </div>

                {isLoadingBooks ? (
                    <div className="flex justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                ) : books && books.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {books.map((book) => (
                            <BookCard key={book.id} book={book} />
                        ))}
                    </div>
                ) : (
                    <Card>
                        <CardContent className="py-8">
                            <p className="text-center text-muted-foreground">
                                You haven't added any books yet.
                            </p>
                        </CardContent>
                    </Card>
                )}
                <AddBookDialog
                    open={isAddBookDialogOpen}
                    onOpenChange={setIsAddBookDialogOpen}
                />
            </div>
        </div>
    );
}
