"use client";

import React, { useState } from 'react';
import {
  Box,
  Button,
  Header,
  SpaceBetween,
  FormField,
  Input,
  Select,
  Textarea,
  Alert,
  ProgressBar,
  Badge,
  ColumnLayout,
  Container
} from "@cloudscape-design/components";
import { API_CONFIG } from "@/constants/api";

interface TestResult {
  action: string;
  success: boolean;
  responseTime: number;
  response: Record<string, unknown>;
  timestamp: Date;
}

interface ActionTest {
  id: string;
  title: string;
  description: string;
  category: string;
  icon: string;
  fields: Array<{
    key: string;
    label: string;
    type: 'text' | 'select';
    required?: boolean;
    defaultValue?: string;
    options?: Array<{ label: string; value: string }>;
  }>;
  getPayload: (formData: Record<string, string>) => Record<string, unknown>;
}

const actionTests: ActionTest[] = [
  {
    id: 'government_verify_nationalid',
    title: 'IPRS National ID Verification',
    description: 'Verify Kenyan National ID with government IPRS system',
    category: 'Government Verification',
    icon: 'check-circle',
    fields: [
      { key: 'idNumber', label: 'ID Number', type: 'text', required: true }
    ],
    getPayload: (data) => ({
      action: 'government_verify_nationalid',
      data: { idNumber: data.idNumber }
    })
  },
  {
    id: 'government_verify_kra',
    title: 'KRA PIN Verification',
    description: 'Verify KRA PIN with Kenya Revenue Authority',
    category: 'Government Verification',
    icon: 'check-circle',
    fields: [
      { key: 'idNumber', label: 'ID Number', type: 'text', required: true },
      { key: 'pin', label: 'KRA PIN', type: 'text', required: true },
      { key: 'taxPayerName', label: 'Taxpayer Name', type: 'text', required: true }
    ],
    getPayload: (data) => ({
      action: 'government_verify_kra',
      data: {
        idNumber: data.idNumber,
        pin: data.pin,
        taxPayerName: data.taxPayerName
      }
    })
  },
  {
    id: 'background_check',
    title: 'Background Check',
    description: 'LexisNexis screening for criminal records, sanctions, PEP',
    category: 'Compliance Checks',
    icon: 'search',
    fields: [
      { key: 'firstName', label: 'First Name', type: 'text', required: true },
      { key: 'lastName', label: 'Last Name', type: 'text', required: true },
      { key: 'gender', label: 'Gender', type: 'select', required: true,
        options: [{ label: 'Male', value: 'Male' }, { label: 'Female', value: 'Female' }] },
      { key: 'nationalId', label: 'National ID', type: 'text', required: true }
    ],
    getPayload: (data) => ({
      action: 'background_check',
      data: {
        firstName: data.firstName,
        lastName: data.lastName,
        gender: data.gender,
        dateOfBirth: '1994-12-19',
        nationalIdentificationNumber: data.nationalId
      }
    })
  },
  {
    id: 'face_liveness',
    title: 'Face Liveness Detection',
    description: 'Create AWS Rekognition face liveness session',
    category: 'Biometric Verification',
    icon: 'camera',
    fields: [],
    getPayload: () => ({
      action: 'face_liveness',
      data: { action: 'create' }
    })
  },
  {
    id: 'validate_nationalid',
    title: 'National ID Document Validation',
    description: 'Validate uploaded National ID document',
    category: 'Document Validation',
    icon: 'file-open',
    fields: [
      { key: 'idNumber', label: 'ID Number', type: 'text', required: true },
      { key: 'documentUrl', label: 'Document URL', type: 'text', required: true }
    ],
    getPayload: (data) => ({
      action: 'validate_nationalid',
      data: {
        idNumber: data.idNumber,
        uploadedDocumentUrl: data.documentUrl
      }
    })
  },
  {
    id: 'validate_passport',
    title: 'Passport Document Validation',
    description: 'Validate uploaded passport document',
    category: 'Document Validation',
    icon: 'file-open',
    fields: [
      { key: 'passportNumber', label: 'Passport Number', type: 'text', required: true },
      { key: 'documentUrl', label: 'Document URL', type: 'text', required: true }
    ],
    getPayload: (data) => ({
      action: 'validate_passport',
      data: {
        passportNumber: data.passportNumber,
        uploadedDocumentUrl: data.documentUrl
      }
    })
  }
];

const UnifiedKYCTesting: React.FC = () => {
  const [formData, setFormData] = useState<Record<string, Record<string, string>>>({});
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  const handleFieldChange = (actionId: string, fieldKey: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [actionId]: {
        ...prev[actionId],
        [fieldKey]: value
      }
    }));
  };

  const runTest = async (actionTest: ActionTest) => {
    const actionId = actionTest.id;
    setLoading(prev => ({ ...prev, [actionId]: true }));

    try {
      const currentFormData = formData[actionId] || {};

      // Validate required fields
      const completeFormData = { ...currentFormData };
      for (const field of actionTest.fields) {
        if (field.required && !completeFormData[field.key]) {
          throw new Error(`${field.label} is required`);
        }
      }

      const payload = actionTest.getPayload(completeFormData);
      const startTime = Date.now();

      const response = await fetch(API_CONFIG.UNIFIED_KYC_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      const endTime = Date.now();
      const responseTime = endTime - startTime;
      const result = await response.json();

      const testResult: TestResult = {
        action: actionId,
        success: result.success || false,
        responseTime,
        response: result,
        timestamp: new Date()
      };

      setTestResults(prev => ({
        ...prev,
        [actionId]: testResult
      }));

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      const testResult: TestResult = {
        action: actionId,
        success: false,
        responseTime: 0,
        response: { error: errorMessage },
        timestamp: new Date()
      };

      setTestResults(prev => ({
        ...prev,
        [actionId]: testResult
      }));
    } finally {
      setLoading(prev => ({ ...prev, [actionId]: false }));
    }
  };

  const groupedActions = actionTests.reduce((acc, action) => {
    if (!acc[action.category]) {
      acc[action.category] = [];
    }
    acc[action.category].push(action);
    return acc;
  }, {} as Record<string, ActionTest[]>);

  const renderActionCard = (actionTest: ActionTest) => {
    const actionId = actionTest.id;
    const result = testResults[actionId];
    const isLoading = loading[actionId];
    const currentFormData = formData[actionId] || {};

    return (
      <Container
        key={actionId}
        header={
          <Header
            variant="h3"
            actions={
              <Box>
                {result && (
                  <Badge color={result.success ? "green" : "red"}>
                    {result.success ? "Success" : "Failed"}
                  </Badge>
                )}
              </Box>
            }
          >
            <Box display="flex" alignItems="center">
              <Box marginRight="s">
                <span className={`awsui-icon awsui-icon-${actionTest.icon}`} />
              </Box>
              {actionTest.title}
            </Box>
          </Header>
        }
      >
        <SpaceBetween size="m">
          <Box variant="p" color="text-body-secondary">
            {actionTest.description}
          </Box>

          {actionTest.fields.length > 0 && (
            <SpaceBetween size="s">
              {actionTest.fields.map(field => (
                <FormField key={field.key} label={field.label}>
                  {field.type === 'select' ? (
                    <Select
                      selectedOption={currentFormData[field.key] ? {
                        label: currentFormData[field.key],
                        value: currentFormData[field.key]
                      } : null}
                      onChange={({ detail }) =>
                        handleFieldChange(actionId, field.key, detail.selectedOption.value || '')
                      }
                      options={field.options || []}
                    />
                  ) : (
                    <Input
                      value={currentFormData[field.key] || ''}
                      onChange={({ detail }) =>
                        handleFieldChange(actionId, field.key, detail.value)
                      }
                      placeholder={field.label}
                    />
                  )}
                </FormField>
              ))}
            </SpaceBetween>
          )}

          <Button
            variant="primary"
            loading={isLoading}
            onClick={() => runTest(actionTest)}
          >
            {isLoading ? 'Testing...' : 'Run Test'}
          </Button>

          {result && (
            <SpaceBetween size="s">
              <Box>
                <Badge color={result.success ? "green" : "red"}>
                  Response Time: {result.responseTime}ms
                </Badge>
              </Box>

              <FormField label="Response">
                <Textarea
                  value={JSON.stringify(result.response, null, 2)}
                  rows={8}
                  readOnly
                />
              </FormField>
            </SpaceBetween>
          )}
        </SpaceBetween>
      </Container>
    );
  };

  // Calculate overall stats
  const totalTests = Object.keys(testResults).length;
  const successfulTests = Object.values(testResults).filter(r => r.success).length;
  const averageResponseTime = totalTests > 0
    ? Math.round(Object.values(testResults).reduce((sum, r) => sum + r.responseTime, 0) / totalTests)
    : 0;

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Test the unified KYC API with real Kenyan government integrations"
      >
        Unified KYC API Testing
      </Header>

      <Alert type="info">
        <Box variant="strong">Real Government Integration</Box>
        <Box>
          This interface tests the <strong>unified action-based KYC endpoint</strong> with real Kenyan government APIs (IPRS, KRA).
          Response times may vary based on government service availability.
        </Box>
      </Alert>

      {totalTests > 0 && (
        <Container header={<Header variant="h2">Test Results Summary</Header>}>
          <ColumnLayout columns={3}>
            <Box textAlign="center">
              <Box fontSize="heading-xl" fontWeight="bold">{totalTests}</Box>
              <Box color="text-body-secondary">Tests Run</Box>
            </Box>
            <Box textAlign="center">
              <Box fontSize="heading-xl" fontWeight="bold" color="text-status-success">
                {successfulTests}
              </Box>
              <Box color="text-body-secondary">Successful</Box>
            </Box>
            <Box textAlign="center">
              <Box fontSize="heading-xl" fontWeight="bold">{averageResponseTime}ms</Box>
              <Box color="text-body-secondary">Avg Response Time</Box>
            </Box>
          </ColumnLayout>
          {totalTests > 0 && (
            <ProgressBar
              value={(successfulTests / totalTests) * 100}
              label="Success Rate"
              description={`${successfulTests}/${totalTests} tests passed`}
              status={successfulTests === totalTests ? "success" : "in-progress"}
            />
          )}
        </Container>
      )}

      {Object.entries(groupedActions).map(([category, actions]) => (
        <Box key={category}>
          <Header variant="h2">{category}</Header>
          <ColumnLayout columns={2}>
            {actions.map(renderActionCard)}
          </ColumnLayout>
        </Box>
      ))}
    </SpaceBetween>
  );
};

export default UnifiedKYCTesting;