"use client"

import React, {useEffect, useState} from 'react';
import {Box, Button, Cards, ColumnLayout, Container, Header, SpaceBetween} from '@cloudscape-design/components';
import {DashboardMetrics} from "@/types/interfaces";
import {fetchMetrics} from "@/services/DataService";


const Dashboard: React.FC = () => {
    const [metrics, setMetrics] = useState<DashboardMetrics>({
        documentValidations: 0,
        documentVerifications: 0,
        backGroundChecks: 0,
        agentRegistrations: 0,
        customerRegistrations: 0,
        apiCalls: 0,
        apiCallsCachehits: 0,
        faceLivenessCount: 0,
    });
    const [loading, setLoading] = useState(true);
    const handleRefresh = async () => {
        setLoading(true);
        try {
            const data = await fetchMetrics();
            setMetrics(data);
        } catch (error) {
            console.error('Failed to refresh metrics:', error);
        } finally {
            setLoading(false);
        }
    };
    useEffect(() => {
        const loadMetrics = async () => {
            try {
                const data = await fetchMetrics();
                setMetrics(data);
            } catch (error) {
                console.error('Error fetching metrics:', error);
            } finally {
                setLoading(false);
            }
        };

        loadMetrics();
    }, []);

    const metricCards = [
        {
            title: 'Document Validations',
            value: metrics.documentValidations,
            description: 'KYC documents checked against uploaded copies',
            icon: 'file-open',
        },
        {
            title: 'Document Verifications',
            value: metrics.documentVerifications,
            description: 'Documents verified against Identity Services',
            icon: 'check-circle',
        },
        {
            title: 'Background Checks',
            value: metrics.backGroundChecks,
            description: 'Completed background verification processes',
            icon: 'search',
        },
        {
            title: 'Agent Registrations',
            value: metrics.agentRegistrations,
            description: 'Total agents registered in the system',
            icon: 'user-profile',
        },
        {
            title: 'Customer Registrations',
            value: metrics.customerRegistrations,
            description: 'Total customers onboarded',
            icon: 'users',
        },
        {
            title: 'API Calls',
            value: metrics.apiCalls,
            description: 'Total external API calls made',
            icon: 'external',
        },
        {
            title: 'API Cache Hits',
            value: metrics.apiCallsCachehits,
            description: 'API calls served from cache',
            icon: 'database',
        },
        {
            title: 'FaceLiveness Sessions',
            value: metrics.faceLivenessCount,
            description: 'Face liveness detection sessions',
            icon: 'camera',
        },
    ];

    return (
        <Container>
            <SpaceBetween size="l">
                <Header
                    variant="h1"
                    description="Overview of KYC system performance and usage"
                    actions={
                        <Button
                            iconName="refresh"
                            loading={loading}
                            onClick={handleRefresh}
                            variant="primary"
                        >
                            Refresh
                        </Button>
                    }
                >
                    eKYC Dashboard
                </Header>

                <Cards
                cardDefinition={{
                    header: item => (
                        <Header
                            variant="h2"
                            actions={
                                <Box color="text-status-info" fontSize="display-l">
                                    <span aria-hidden="true" className={`awsui-icon awsui-icon-${item.icon}`} />
                                </Box>
                            }
                        >
                            {item.title}
                        </Header>
                    ),
                    sections: [
                        {
                            id: "value",
                            header: "Count",
                            content: item => (
                                <Box variant="awsui-key-label" color="text-status-success">
                                    <span style={{fontSize: '2.5rem', fontWeight: 'bold'}}>
                                        {loading ? '—' : item.value.toLocaleString()}
                                    </span>
                                </Box>
                            )
                        },
                        {
                            id: "description",
                            content: item => (
                                <Box color="text-body-secondary" fontSize="body-m">
                                    {item.description}
                                </Box>
                            )
                        }
                    ]
                }}
                items={metricCards}
                loadingText="Loading metrics"
                loading={loading}
                cardsPerRow={[
                    { cards: 1 },
                    { minWidth: 500, cards: 2 },
                    { minWidth: 992, cards: 4 }
                ]}
            />

            <ColumnLayout columns={2}>
                {/* You can add charts or other visualizations here */}
            </ColumnLayout>
            </SpaceBetween>
        </Container>
    );
};

export default Dashboard;

