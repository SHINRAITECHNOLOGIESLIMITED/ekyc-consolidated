// components/ErrorAlert.tsx
import { Alert } from "@cloudscape-design/components";

interface ErrorAlertProps {
  error: string;
  onDismiss: () => void;
}

export function ErrorAlert({ error, onDismiss }: ErrorAlertProps) {
  return (
    <Alert
      type="error"
      header="Error"
      dismissible
      onDismiss={onDismiss}
    >
      {error}
    </Alert>
  );
}
