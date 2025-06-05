import React from "react";
import DocumentValidationForm from "./DocumentValidationForm";

export const NationalIdValidationForm: React.FC = () => (
  <DocumentValidationForm
    title="National ID Validation"
    documentType="nationalid"
    apiEndpoint="/api/document/nationalid"
    fields={[
      { id: "serialNumber", label: "Serial Number", required: true },
      { id: "idNumber", label: "ID Number", required: true },
      { id: "fullNames", label: "Full Names", required: true },
      { id: "dateOfBirth", label: "Date of Birth", type: "date", required: true },
      { id: "dateOfIssue", label: "Date of Issue", type: "date", required: true },
      { id: "gender", label: "Gender", required: true },
      { id: "districtOfBirth", label: "District of Birth", required: true },
      { id: "placeOfIssue", label: "Place of Issue", required: true },
    ]}
  />
);

export const PassportValidationForm: React.FC = () => (
  <DocumentValidationForm
    title="Passport Validation"
    documentType="passport"
    apiEndpoint="/api/document/passport"
    fields={[
      { id: "documentType", label: "Document Type", required: true },
      { id: "countryCode", label: "Country Code", required: true },
      { id: "passportNumber", label: "Passport Number", required: true },
      { id: "personalNumber", label: "Personal Number", required: true },
      { id: "surname", label: "Surname", required: true },
      { id: "givenNames", label: "Given Names", required: true },
      { id: "gender", label: "Gender", required: true },
      { id: "dateOfBirth", label: "Date of Birth", type: "date", required: true },
      { id: "placeOfBirth", label: "Place of Birth", required: true },
      { id: "dateOfIssue", label: "Date of Issue", type: "date", required: true },
      { id: "dateOfExpiry", label: "Date of Expiry", type: "date", required: true },
      { id: "nationality", label: "Nationality", required: true },
      { id: "issuingAuthority", label: "Issuing Authority", required: true },
    ]}
  />
);

export const KRAPinCertificateValidationForm: React.FC = () => (
  <DocumentValidationForm
    title="KRA Pin Certificate Validation"
    documentType="krapincertificate"
    apiEndpoint="/api/document/krapincertificate"
    fields={[
      { id: "certificateDate", label: "Certificate Date", type: "date", required: true },
      { id: "pin", label: "PIN", required: true },
      { id: "taxPayerName", label: "Tax Payer Name", required: true },
      { id: "emailAddress", label: "Email Address", required: true },
    ]}
  />
);

export const CR12ValidationForm: React.FC = () => (
  <DocumentValidationForm
    title="Certificate of Incorporation (CR12) Validation"
    documentType="cr12"
    apiEndpoint="/api/document/cr12"
    fields={[
      { id: "businessNumber", label: "Business Number", required: true },
      { id: "businessName", label: "Business Name", required: true },
    ]}
  />
);