import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Loader2 } from "lucide-react";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

type Book = {
    id?: string;
    title: string;
    author: string;
    description: string;
    ownerId: number;
    createdAt: Date;
};

type AddToShelfDialogProps = {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    shelfId?: string;
};

export default function AddToShelfDialog({
    open,
    onOpenChange,
    shelfId,
}: AddToShelfDialogProps) {
    const { toast } = useToast();
    const queryClient = useQueryClient();
    const [selectedBook, setSelectedBook] = useState<string>("");
    const [isAdding, setIsAdding] = useState(false);

    const { data: books = [], isLoading } = useQuery<Book[]>({
        queryKey: ["/api/books"],
        enabled: open,
    });

    const addToShelfMutation = useMutation({
        mutationFn: async () => {
            const response = await fetch(`/api/shelves/${shelfId}/books`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ bookId: selectedBook }),
                credentials: "include",
            });

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
                description: "Book added to shelf successfully",
            });
            onOpenChange(false);
        },
        onError: (error: Error) => {
            toast({
                title: "Error",
                description: error.message,
                variant: "destructive",
            });
        },
        onSettled: () => {
            setIsAdding(false);
            setSelectedBook("");
        },
    });

    const handleAddToShelf = async () => {
        if (!selectedBook) {
            toast({
                title: "Error",
                description: "Please select a book",
                variant: "destructive",
            });
            return;
        }

        setIsAdding(true);
        await addToShelfMutation.mutateAsync();
    };

    if (isLoading) {
        return (
            <Dialog open={open} onOpenChange={onOpenChange}>
                <DialogContent>
                    <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin" />
                    </div>
                </DialogContent>
            </Dialog>
        );
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Add Book to Shelf</DialogTitle>
                    <DialogDescription>
                        Select one of your books to add to this shelf.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                    <Select
                        value={selectedBook}
                        onValueChange={setSelectedBook}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="Select a book" />
                        </SelectTrigger>
                        <SelectContent>
                            {books.map((book) => (
                                <SelectItem
                                    key={book.id}
                                    value={String(book.id)}
                                >
                                    {book.title} by {book.author}
                                </SelectItem>
                            ))}
                            {books.length === 0 && (
                                <SelectItem value="" disabled>
                                    No books available. Create books in your
                                    profile first.
                                </SelectItem>
                            )}
                        </SelectContent>
                    </Select>
                    <Button
                        onClick={handleAddToShelf}
                        className="w-full"
                        disabled={isAdding || !selectedBook}
                    >
                        {isAdding ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Adding...
                            </>
                        ) : (
                            "Add to Shelf"
                        )}
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
