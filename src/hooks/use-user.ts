import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
type User = {
    id: string;
    username: string;
    password: string;
    telegram_contact: string | null;
    created_At: Date;
};

type LoginData = {
    username: string;
    password: string;
    telegramContact?: string;
};

type RequestResult =
    | {
          ok: true;
      }
    | {
          ok: false;
          message: string;
      };

async function handleRequest(
    url: string,
    method: string,
    body?: LoginData,
): Promise<RequestResult> {
    try {
        const response = await fetch(url, {
            method,
            headers: body ? { "Content-Type": "application/json" } : undefined,
            body: body ? JSON.stringify(body) : undefined,
            credentials: "include",
        });

        if (!response.ok) {
            if (response.status >= 500) {
                return { ok: false, message: response.statusText };
            }

            const message = await response.text();
            return { ok: false, message };
        }

        return { ok: true };
    } catch (e: any) {
        return { ok: false, message: e.toString() };
    }
}

async function fetchUser(): Promise<User | null> {
    const response = await fetch("http://localhost:8000/api/user/profile", {
        credentials: "include",
    });

    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            return null;
        }

        throw new Error(`${response.status}: ${await response.text()}`);
    }

    return response.json();
}

export function useUser() {
    const queryClient = useQueryClient();

    const {
        data: user,
        error,
        isLoading,
    } = useQuery<User | null, Error>({
        queryKey: ["user"],
        queryFn: fetchUser,
        staleTime: 5 * 60 * 1000,
        retry: true,
    });

    const loginMutation = useMutation<RequestResult, Error, LoginData>({
        mutationFn: (userData) =>
            handleRequest("http://localhost:8000/api/login", "POST", userData),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["user"] });
        },
    });

    const logoutMutation = useMutation<RequestResult, Error>({
        mutationFn: () =>
            handleRequest("http://localhost:8000/api/logout", "POST"),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["user"] });
        },
    });

    const registerMutation = useMutation<RequestResult, Error, LoginData>({
        mutationFn: (userData) =>
            handleRequest(
                "http://localhost:8000/api/register",
                "POST",
                userData,
            ),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["user"] });
        },
    });

    return {
        user,
        isLoading,
        error,
        login: loginMutation.mutateAsync,
        logout: logoutMutation.mutateAsync,
        register: registerMutation.mutateAsync,
    };
}
