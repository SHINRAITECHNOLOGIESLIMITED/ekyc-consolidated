"use client";

import Listing, { ListingProps } from "@/components/Listing";
import { fetchDocumentValidations } from "@/services/DataService";
import type { DocumentValidation } from "@/types/models";
import { SpaceBetween } from "@cloudscape-design/components";
import ValidationDetails from "./ValidationDetails";
import { formatPercentage } from "@/utils/formatters";
import { 
  NationalIdValidationForm, 
  PassportValidationForm, 
  KRAPinCertificateValidationForm, 
  CR12ValidationForm 
} from "@/components/DocumentValidationForms";

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
      render: () => (
        <SpaceBetween size={"s"}>
          <NationalIdValidationForm />
        </SpaceBetween>
      ),
    },
    {
      label: "New Passport Validation",
      id: "passport", // Add an id to each action
      render: () => (
        <SpaceBetween size={"s"}>
          <PassportValidationForm />
        </SpaceBetween>
      ),
    },
    {
      label: "New KRAPinCertificate Validation",
      id: "krapincertificate", // Add an id to each action
      render: () => (
        <SpaceBetween size={"s"}>
          <KRAPinCertificateValidationForm />
        </SpaceBetween>
      ),
    },
    {
      label: "Certification of Incoporation (CR12) Validation",
      id: "cr12", // Add an id to each action
      render: () => (
        <SpaceBetween size={"s"}>
          <CR12ValidationForm />
        </SpaceBetween>
      ),
    },
  ],
};


const DocumentsListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default DocumentsListing;
