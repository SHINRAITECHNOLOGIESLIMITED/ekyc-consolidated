"use client";

import Listing, { ListingProps } from "@/components/Listing";
import { fetchDocumentVerifications } from "@/services/DataService";
import type { DocumentVerification } from "@/types/models";
import VerificationDetails from "./VerificationDetails";
import { formatPercentage } from "@/utils/formatters";
import DocumentForm from "@/components/DocumentForm";

const columnDefinitions = [
  {
    id: "VerificationId",
    header: "Verification ID",
    cell: (item: DocumentVerification) => item.verificationId,
  },
  {
    id: "documentType",
    header: "Verification Type",
    cell: (item: DocumentVerification) => item.documentType,
  },
  {
    id: "documentIdentifier",
    header: "Identifier",
    cell: (item: DocumentVerification) => item.documentIdentifier ?? "",
  },
  {
    id: "accuracy",
    header: "Accuracy",
    cell: (item: DocumentVerification) =>
      formatPercentage(item.processing_accuracy),
  },
  {
    id: "accuracy",
    header: "Validity",
    cell: (item: DocumentVerification) =>
      formatPercentage(item.validation_accuracy),
  },
];

const listingProps: ListingProps<DocumentVerification> = {
  title: "Verifications",
  getAll: fetchDocumentVerifications,
  pageSize: 100,
  columnDefinitions,
  itemKey: (item: DocumentVerification) => item.verificationId.toString(),
  itemDetailsLink: (item: DocumentVerification) =>
    `doc-verifications/${item.verificationId}`,
  renderItemDetails: (item: DocumentVerification) => VerificationDetails(item),

  actions: [
    {
      label: "New NationalId Verification",
      id: "nationalid",
      render: () => {
        return <NationalIdVerificationForm />;
      },
    },
    {
      label: "New Passport Verification",
      id: "passport",
      render: () => {
        return <PassportVerificationForm />;
      },
    },
    {
      label: "New KRA Info Verification",
      id: "krapincertificate",
      render: () => {
        return <KRAVerificationForm />;
      },
    },
  ],
};

const NationalIdVerificationForm: React.FC = () => (
  <DocumentForm
    title="National ID Verification"
    apiEndpoint="government/nationalid"
    fields={[
      { id: "idNumber", label: "ID Number", type: "text", required: true, placeholder: "23667272" },
      { id: "serialNumber", label: "Serial Number", type: "text", placeholder: "217934147" },
      { id: "fullNames", label: "Full Names", type: "text", placeholder: "JANE WAIRIMU MAINA" },
      { id: "dateOfBirth", label: "Date of Birth", type: "date", placeholder: "1985-01-01" },
      { id: "dateOfIssue", label: "Date of Issue", type: "date", placeholder: "2016-10-28" },
      { id: "gender", label: "Gender", type: "text", placeholder: "Female" },
      { id: "districtOfBirth", label: "District of Birth", type: "text", placeholder: "THIKA WEST" },
    ]}
  />
);

const PassportVerificationForm: React.FC = () => (
  <DocumentForm
    title="Passport Verification"
    apiEndpoint="government/passport"
    fields={[
      { id: "passportNumber", label: "Passport Number", type: "text", required: true, placeholder: "BK120129" },
      { id: "idNumber", label: "ID Number", type: "text", required: true, placeholder: "23667272" },
      { id: "firstName", label: "First Name", type: "text", placeholder: "GEORGE" },
      { id: "otherName", label: "Other Name", type: "text", placeholder: "HUMPHREY" },
      { id: "surname", label: "Surname", type: "text", placeholder: "KAJIMBA" },
      { id: "gender", label: "Gender", type: "text", placeholder: "M" },
      { id: "dateOfBirth", label: "Date of Birth", type: "date", placeholder: "1987-05-18" },
      { id: "dateOfIssue", label: "Date of Issue", type: "date", placeholder: "2020-08-20" },
      { id: "dateOfExpiry", label: "Date of Expiry", type: "date", placeholder: "2030-09-03" },
    ]}
  />
);

const KRAVerificationForm: React.FC = () => (
  <DocumentForm
    title="KRA Verification"
    apiEndpoint="government/kra"
    fields={[
      { id: "idNumber", label: "ID Number", type: "text", required: true, placeholder: "23667272" },
      { id: "pin", label: "PIN", type: "text", placeholder: "A003388522V" },
      { id: "taxPayerName", label: "Tax Payer Name", type: "text", placeholder: "Jackson Gitonga Mwangi" },
    ]}
  />
);

const DocumentsListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default DocumentsListing;
