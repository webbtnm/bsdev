import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Trash2 } from "lucide-react";
import { useUser } from "@/hooks/use-user";
import { useState } from "react";

type Book = {
    id?: string;
    title: string;
    author: string;
    description: string;
    ownerId: string;
    createdAt: Date;
};

export interface BookCardProps {
    book: Book;
    shelfId?: string;
    onRemove?: () => void;
}

export function BookCard({ book, shelfId, onRemove }: BookCardProps) {
    const { user } = useUser();
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [isRemoveDialogOpen, setIsRemoveDialogOpen] = useState(false);

    const isOwner = book.ownerId === user?.id;

    const removeFromShelfMutation = useMutation({
        mutationFn: async () => {
            const response = await fetch(
                `/api/shelves/${shelfId}/books/${book.id}`,
                {
                    method: "DELETE",
                    credentials: "include",
                },
            );

            if (!response.ok) {
                throw new Error(await response.text());
            }

            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: [`/api/shelves/${shelfId}/books`],
            });
            toast({
                title: "Success",
                description: "Book removed from shelf",
            });
            onRemove?.();
        },
        onError: (error: Error) => {
            toast({
                title: "Error",
                description: error.message,
                variant: "destructive",
            });
        },
    });

    const deleteBookMutation = useMutation({
        mutationFn: async () => {
            const response = await fetch(`/api/books/${book.id}`, {
                method: "DELETE",
                credentials: "include",
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            return response.json();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["/api/books"] });
            if (shelfId) {
                queryClient.invalidateQueries({
                    queryKey: [`/api/shelves/${shelfId}/books`],
                });
            }
            toast({
                title: "Success",
                description: "Book deleted successfully",
            });
            onRemove?.();
        },
        onError: (error: Error) => {
            toast({
                title: "Error",
                description: error.message,
                variant: "destructive",
            });
        },
    });

    return (
        <>
            <Card>
                <CardContent className="p-4">
                    <h3 className="font-bold mb-2">{book.title}</h3>
                    <p className="text-sm text-muted-foreground mb-2">
                        by {book.author}
                    </p>
                    {book.description && (
                        <p className="text-sm text-muted-foreground mb-4">
                            {book.description}
                        </p>
                    )}
                    <div className="flex justify-end gap-2">
                        {shelfId && (
                            <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => setIsRemoveDialogOpen(true)}
                                disabled={removeFromShelfMutation.isPending}
                            >
                                {removeFromShelfMutation.isPending ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <>
                                        <Trash2 className="h-4 w-4 mr-1" />
                                        Remove from Shelf
                                    </>
                                )}
                            </Button>
                        )}
                        {isOwner && (
                            <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => setIsDeleteDialogOpen(true)}
                                disabled={deleteBookMutation.isPending}
                            >
                                {deleteBookMutation.isPending ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <>
                                        <Trash2 className="h-4 w-4 mr-1" />
                                        Delete Book
                                    </>
                                )}
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>

            <AlertDialog
                open={isRemoveDialogOpen}
                onOpenChange={setIsRemoveDialogOpen}
            >
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>
                            Remove Book from Shelf
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to remove "{book.title}" from
                            this shelf? This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={() => removeFromShelfMutation.mutate()}
                        >
                            Remove
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            <AlertDialog
                open={isDeleteDialogOpen}
                onOpenChange={setIsDeleteDialogOpen}
            >
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Book</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete "{book.title}"? This
                            will remove it from all shelves and cannot be
                            undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            onClick={() => deleteBookMutation.mutate()}
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}

export default BookCard;
