"use client";

import DocumentForm from "@/components/DocumentForm";


const SystemSettings = () => {
    return (
        <SettingsForm/>
    );
};
const SettingsForm: React.FC = () => (
  <DocumentForm
    title="System Settings"
    apiEndpoint="settings"
    fields={[
      { id: "livenessThreshold", label: "Liveness Threshold", type: "text", placeholder: "70.0 %" },
      { id: "validationThreshold", label: "Validation Threshold", type: "text",  placeholder: "85.0 %"  }
    ]}
  />
);

export default SystemSettings;