"use client";

import { fetchMetrics } from "@/services/DataService";
import { DashboardMetrics } from "@/types/interfaces";
import {
  Box,
  Button,
  Cards,
  ColumnLayout,
  Header,
  ProgressBar,
  SpaceBetween,
} from "@cloudscape-design/components";
import React, { useEffect, useState } from "react";

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
      console.error("Failed to refresh metrics:", error);
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
        console.error("Error fetching metrics:", error);
      } finally {
        setLoading(false);
      }
    };

    loadMetrics();
  }, []);

  // Calculate cache hit rate percentage
  const cacheHitRate =
    metrics.apiCalls > 0
      ? Math.round((metrics.apiCallsCachehits / metrics.apiCalls) * 100)
      : 0;

  // Group 1: Registration Metrics
  const registrationMetrics = [
    {
      title: "Agent Registrations",
      value: metrics.agentRegistrations,
      description: "Total agents registered in the system",
      icon: "user-profile",
    },
    {
      title: "Customer Registrations",
      value: metrics.customerRegistrations,
      description: "Total customers onboarded",
      icon: "users",
    },
  ];

  // Group 2: Document Processing Metrics (includes Face Liveness)
  const documentMetrics = [
    {
      title: "Document Validations",
      value: metrics.documentValidations,
      description: "KYC documents checked against uploaded copies",
      icon: "file-open",
    },
    {
      title: "Document Verifications",
      value: metrics.documentVerifications,
      description: "Documents verified against Identity Services",
      icon: "check-circle",
    },
    {
      title: "Background Checks",
      value: metrics.backGroundChecks,
      description: "Completed background verification processes",
      icon: "search",
    },
    {
      title: "Face Liveness Sessions",
      value: metrics.faceLivenessCount,
      description: "Face liveness detection sessions completed",
      icon: "camera",
    },
  ];

  // Group 3: API Performance Metrics
  const apiMetrics = {
    items: [
      { name: "Total API Calls", value: metrics.apiCalls },
      { name: "Cache Hits", value: metrics.apiCallsCachehits },
      { name: "Cache Hit Rate", value: `${cacheHitRate}%` },
    ],
  };

  return (
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

      {/* Registrations Section - Moved to top */}
      <Box padding="s">
        <SpaceBetween size="m">
          <Header variant="h2">Registrations</Header>
          <Cards
            cardDefinition={{
              header: (item) => (
                <Header
                  variant="h3"
                  actions={
                    <Box color="text-status-info" fontSize="display-l">
                      <span
                        aria-hidden="true"
                        className={`awsui-icon awsui-icon-${item.icon}`}
                      />
                    </Box>
                  }
                >
                  {item.title}
                </Header>
              ),
              sections: [
                {
                  id: "value",
                  content: (item) => (
                    <Box variant="awsui-key-label">
                      <span style={{ fontSize: "2.5rem", fontWeight: "bold" }}>
                        {loading ? "—" : item.value.toLocaleString()}
                      </span>
                    </Box>
                  ),
                },
                {
                  id: "description",
                  content: (item) => (
                    <Box color="text-body-secondary" fontSize="body-m">
                      {item.description}
                    </Box>
                  ),
                },
              ],
            }}
            items={registrationMetrics}
            loadingText="Loading metrics"
            loading={loading}
            cardsPerRow={[{ cards: 1 }, { minWidth: 500, cards: 2 }]}
          />
        </SpaceBetween>
      </Box>

      {/* Document Processing Section */}
      <Box padding="s">
        <SpaceBetween size="m">
          <Header variant="h2">Core Processing</Header>
          <Cards
            cardDefinition={{
              header: (item) => (
                <Header
                  variant="h3"
                  actions={
                    <Box color="text-status-info" fontSize="display-l">
                      <span
                        aria-hidden="true"
                        className={`awsui-icon awsui-icon-${item.icon}`}
                      />
                    </Box>
                  }
                >
                  {item.title}
                </Header>
              ),
              sections: [
                {
                  id: "value",
                  content: (item) => (
                    <Box variant="awsui-key-label">
                      <span style={{ fontSize: "2.5rem", fontWeight: "bold" }}>
                        {loading ? "—" : item.value.toLocaleString()}
                      </span>
                    </Box>
                  ),
                },
                {
                  id: "description",
                  content: (item) => (
                    <Box color="text-body-secondary" fontSize="body-m">
                      {item.description}
                    </Box>
                  ),
                },
              ],
            }}
            items={documentMetrics}
            loadingText="Loading metrics"
            loading={loading}
            cardsPerRow={[
              { cards: 1 },
              { minWidth: 500, cards: 2 },
              { minWidth: 992, cards: 4 },
            ]}
          />
        </SpaceBetween>
      </Box>

      {/* System Performance Section - More compact API section */}
      <Box padding="s">
        <SpaceBetween size="m">
          <Header variant="h2">System Performance</Header>
          <Box
            padding="m"
          >
            <SpaceBetween size="s">
              <Header variant="h3">API Performance</Header>
              <ColumnLayout columns={3}>
                {apiMetrics.items.map((item, index) => (
                  <Box key={index} textAlign="center">
                    <Box fontSize="heading-s" fontWeight="bold">
                      {item.name}
                    </Box>
                    <Box fontSize="heading-xl">{item.value}</Box>
                  </Box>
                ))}
              </ColumnLayout>
              <ProgressBar
                value={cacheHitRate}
                label="Cache Efficiency"
                description={`${cacheHitRate}% of API calls served from cache`}
                status={cacheHitRate > 50 ? "success" : "in-progress"}
              />
            </SpaceBetween>
          </Box>
        </SpaceBetween>
      </Box>

      {/* Future placeholder for charts or additional visualizations */}
      <Box padding="s">
        <Header variant="h2">Trends & Analytics</Header>
        <Box padding="xxl" textAlign="center" color="text-body-secondary">
          Charts and trend analysis will be displayed here
        </Box>
      </Box>
    </SpaceBetween>
  );
};

export default Dashboard;
