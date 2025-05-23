export const formatTimeStamp = (timestamp: number): string => {
    try {
        const dateObj = new Date(timestamp * 1000);
        return dateObj.toLocaleString('en-US', {
            month: 'short',    // "Apr"
            day: 'numeric',    // "11"
            year: 'numeric',   // "2025"
            hour: '2-digit',   // "12"
            minute: '2-digit', // "59"
            second: '2-digit', // "06"
            hour12: true       // Use 12-hour format with AM/PM
        });
    } catch (e) {
        console.error(`Error formatting date ${timestamp}:`, e);
        return timestamp.toString();
    }
};


export const formatDateTime = (date: string): string => {
    try {
        return new Date(date).toLocaleString('en-US', {
            month: 'short',    // "Apr"
            day: 'numeric',    // "11"
            year: 'numeric',   // "2025"
            hour: '2-digit',   // "12"
            minute: '2-digit', // "59"
            second: '2-digit', // "06"
            hour12: true       // Use 12-hour format with AM/PM
        });
    } catch (e) {
        console.error(`Error formatting date ${date}:`, e);
        return date.toString();
    }
};


export const formatUUID = (uuid: string) => {
    if (!uuid) return "-";
    return `${uuid.slice(0, 6)}...${uuid.slice(-4)}`;
};

export const formatPercentage = (value: number) => {
    //return rounded of to 1 decimal place
    return (Math.round(value * 100) / 100).toFixed(1);
};