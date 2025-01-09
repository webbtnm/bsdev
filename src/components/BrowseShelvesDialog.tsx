//import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
//import { useToast } from "@/hooks/use-toast";
import { Loader2 } from "lucide-react";

type Shelf = {
  id: string,
  name: string,
  description: string,
  ownerId: string,
  public: boolean,
  createdAt: Date
}


type BrowseShelvesDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export default function BrowseShelvesDialog({
  open,
  onOpenChange,
}: BrowseShelvesDialogProps) {
  //const { toast } = useToast();

  const { data: publicShelves = [], isLoading } = useQuery<Shelf[]>({
    queryKey: ["/api/public-shelves"],
    enabled: open,
  });

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
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Browse Public Shelves</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {publicShelves.length > 0 ? (
            publicShelves.map((shelf) => (
              <Card key={shelf.id} className="transition-shadow hover:shadow-lg">
                <CardHeader>
                  <CardTitle className="text-xl">{shelf.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-4">
                    {shelf.description}
                  </p>
                  <Button
                    variant="secondary"
                    className="w-full"
                    onClick={() => {
                      onOpenChange(false);
                    }}
                  >
                    View Shelf
                  </Button>
                </CardContent>
              </Card>
            ))
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No public shelves available
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
