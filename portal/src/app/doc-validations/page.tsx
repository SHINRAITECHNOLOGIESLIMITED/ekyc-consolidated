"use client";

import Listing, { ListingProps } from "@/components/Listing";
import { fetchDocumentValidations } from "@/services/DataService";
import type { DocumentValidation } from "@/types/models";
import ValidationDetails from "./ValidationDetails";
import { formatPercentage } from "@/utils/formatters";
import DocumentValidationForm from "@/components/DocumentValidationForm";

const columnDefinitions = [
  {
    id: "validationId",
    header: "Validation ID",
    cell: (item: DocumentValidation) => item.validationId,
  },
  {
    id: "documentType",
    header: "Document Type",
    cell: (item: DocumentValidation) => item.documentType,
  },
  {
    id: "documentIdentifier",
    header: "Identifier",
    cell: (item: DocumentValidation) => item.documentIdentifier,
  },
  {
    id: "processing_accuracy",
    header: "Accuracy",
    cell: (item: DocumentValidation) => formatPercentage(item.processing_accuracy),
  },
  {
    id: "validation_accuracy",
    header: "Validity",
    cell: (item: DocumentValidation) => formatPercentage(item.validation_accuracy),
  },
  {
    id: "confidence",
    header: "Confidence",
    cell: (item: DocumentValidation) => formatPercentage(item.overall_confidence),
  },
  {
    id: "path",
    header: "S3 Path",
    cell: (item: DocumentValidation) => item.s3Path,
  },
];

const listingProps: ListingProps<DocumentValidation> = {
  title: "Documents Validations",
  getAll: fetchDocumentValidations,
  pageSize: 100,
  columnDefinitions,
  itemKey: (item: DocumentValidation) => item.validationId.toString(),
  itemDetailsLink: (item: DocumentValidation) =>
    `doc-validations/${item.validationId}`,
  renderItemDetails: (item: DocumentValidation) => ValidationDetails(item),
  actions: [
    {
      label: "New NationalId Validation",
      id: "nationalid", // Add an id to each action
      render: () => {
        return (
          <NationalIdValidationForm/>
        );
      },
    },
    {
      label: "New Passport Validation",
      id: "passport", // Add an id to each action
      render: () => {
        return (
          <PassportValidationForm/>
        );
      },
    },
    {
      label: "New KRAPinCertificate Validation",
      id: "krapincertificate", // Add an id to each action
      render: () => {
        return (
          <KRAPinCertificateValidationForm/>
        );
      },
    },
    {
      label: "Certification of Incoporation (CR12) Validation",
      id: "cr12", // Add an id to each action
      render: () => {
        return (
          <CR12ValidationForm/>
        );
      },
    },
  ],
};


const DocumentsListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

const NationalIdValidationForm: React.FC = () => (
  <DocumentValidationForm
    title="National ID Validation"
    documentType="nationalid"
    fields={[
      { id: "idNumber", label: "ID Number", required: true, placeholder: "23667272" },
      { id: "serialNumber", label: "Serial Number", placeholder: "217934147" },
      { id: "fullNames", label: "Full Names", placeholder: "JANE WAIRIMU MAINA" },
      { id: "dateOfBirth", label: "Date of Birth", type: "date", placeholder: "1985-01-01" },
      { id: "dateOfIssue", label: "Date of Issue", type: "date", placeholder: "2016-10-28" },
      { id: "gender", label: "Gender", placeholder: "Female" },
      { id: "districtOfBirth", label: "District of Birth", placeholder: "THIKA WEST" },
      { id: "placeOfIssue", label: "Place of Issue", placeholder: "NGENDA" },
    ]}
  />
);

const PassportValidationForm: React.FC = () => (
  <DocumentValidationForm
    title="Passport Validation"
    documentType="passport"
    fields={[
      { id: "passportNumber", label: "Passport Number", required: true, placeholder: "BK120129" },
      { id: "documentType", label: "Document Type", placeholder: "P" },
      { id: "countryCode", label: "Country Code", placeholder: "KEN" },
      { id: "personalNumber", label: "Personal Number", placeholder: "1736740" },
      { id: "surname", label: "Surname", placeholder: "KAJIMBA" },
      { id: "givenNames", label: "Given Names", placeholder: "GEORGE HUMPHREY" },
      { id: "gender", label: "Gender", placeholder: "M" },
      { id: "dateOfBirth", label: "Date of Birth", type: "date", placeholder: "1987-05-18" },
      { id: "placeOfBirth", label: "Place of Birth", placeholder: "M MIGORI, Ken" },
      { id: "dateOfIssue", label: "Date of Issue", type: "date", placeholder: "2020-08-20" },
      { id: "dateOfExpiry", label: "Date of Expiry", type: "date", placeholder: "2030-09-03" },
      { id: "nationality", label: "Nationality", placeholder: "KENYAN" },
      { id: "issuingAuthority", label: "Issuing Authority", placeholder: "GOVERNMENT OF KENYA" },
    ]}
  />
);

const KRAPinCertificateValidationForm: React.FC = () => (
  <DocumentValidationForm
    title="KRA Pin Certificate Validation"
    documentType="krapincertificate"
    fields={[
      { id: "pin", label: "PIN", required: true, placeholder: "A003388522V" },
      { id: "certificateDate", label: "Certificate Date", type: "date", placeholder: "2014-10-14" },
      { id: "taxPayerName", label: "Tax Payer Name", placeholder: "Jackson Gitonga Mwangi" },
      { id: "emailAddress", label: "Email Address", placeholder: "jackmwangi02@gmail.com" },
    ]}
  />
);

const CR12ValidationForm: React.FC = () => (
  <DocumentValidationForm
    title="Certificate of Incorporation (CR12) Validation"
    documentType="cr12"
    fields={[
      { id: "businessNumber", label: "Business Number", required: true, placeholder: "PVT-RXUMYGVQ" },
      { id: "businessName", label: "Business Name", placeholder: "DETALI INSURANCE AGENCY LIMITED" },
    ]}
  />
);
export default DocumentsListing;
