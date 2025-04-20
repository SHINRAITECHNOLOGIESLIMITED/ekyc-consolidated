import { Alert, StatusIndicator } from "@cloudscape-design/components";
import React, { useEffect, useState } from "react";

export interface DetailsProps<T> {
    title: string;
    primaryKey: string;
    fetcher: (key: string) => Promise<T | null>;
    itemDetails: (item: T) => React.JSX.Element;
}

export const Details = <T,>({ title, primaryKey, fetcher, itemDetails }: DetailsProps<T>) => {
    const [item, setItem] = useState<T>();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);


    useEffect(() => {
        const fetchItem = async () => {
            try {
                const data = await fetcher(primaryKey);
                if (data) {
                    setItem(data);
                } else {
                    setError(`Could not find data for ${title.toLowerCase()} ${primaryKey}`);
                }
            } catch (err) {
                setError(`Failed to fetch ${title.toLowerCase()} data with id ${primaryKey}: ${err}`);
            } finally {
                setLoading(false);
            }
        };

        fetchItem();
    }, [primaryKey,fetcher,title]);

    if (loading) return (
        <StatusIndicator type="loading">
            Loading {title.toLowerCase()} {primaryKey}...
        </StatusIndicator>
    );
    if (error) return (
        <Alert
            type="error"
            header="Error"
            dismissible={false}
        >
            {error}
        </Alert>
    );
    if (!item) return (
        <Alert
            type="error"
            header="Error"
            dismissible={false}
        >
            Could not find {title.toLowerCase()} {primaryKey}
        </Alert>
    );


    return itemDetails(item);

}