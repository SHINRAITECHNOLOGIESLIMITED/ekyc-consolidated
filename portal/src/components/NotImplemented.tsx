import {
    Container,
    Header,
    Box,
    Alert,
    SpaceBetween,
    StatusIndicator
} from '@cloudscape-design/components';

interface NotImplementedProps {
    title: string;
    description?: string;
}

export default function NotImplemented({ title, description }: NotImplementedProps) {
    return (
        <Container
            header={
                <Header
                    variant="h1"
                    description={description || "This feature is currently under development"}
                >
                    {title}
                </Header>
            }
        >
            <SpaceBetween size="l">
                <Alert
                    type="warning"
                    header="Feature not implemented"
                >
                    This page or feature is not yet implemented and is currently under development.
                </Alert>

                <Box margin={{ top: 's' }}>
                    <SpaceBetween size="m">
                        <StatusIndicator type="pending">
                            Development in progress
                        </StatusIndicator>

                        <p>Please check back later or contact the development team for more information.</p>
                    </SpaceBetween>
                </Box>
            </SpaceBetween>
        </Container>
    );
}
