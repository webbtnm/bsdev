export type Book = {
    id: string;
    title: string;
    author: string;
    description: string;
    ownerId: string;
    createdAt: Date;
};
export type Shelf = {
    id: string;
    name: string;
    description: string;
    ownerId: string;
    public: boolean;
    createdAt: Date;
};

export type ShelvesResponse = {
    shelves: Shelf[];
};

export type Member = {
    id: string;
    username: string;
    telegram_contact?: string;
};

export type UserDTO = {
    id: string;
    username: string;
    telegram_contact: string;
};

export type AuthFormData = {
    username: string;
    password: string;
    telegram_contact?: string;
};
