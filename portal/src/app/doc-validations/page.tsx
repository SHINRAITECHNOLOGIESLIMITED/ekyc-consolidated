"use client";

import Listing, { ListingProps } from "@/components/Listing";
import NotImplemented from "@/components/NotImplemented";
import { fetchDocumentValidations } from "@/services/DataService";
import type { DocumentValidation } from "@/types/models";
import { SpaceBetween } from "@cloudscape-design/components";
import ValidationDetails from "./ValidationDetails";

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
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented title={"NationalID Validation"} />
        </SpaceBetween>
      ),
    },
    {
      label: "New Passport Validation",
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented title={"Passport Validation"} />
        </SpaceBetween>
      ),
    },
    {
      label: "New KRAPinCertificate Validation",
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented title={"KRAPinCertificate Validation"} />
        </SpaceBetween>
      ),
    },
    {
      label: "Certification of Incoporation (CR12) Validation",
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented
            title={"New Certification of Incoporation (CR12) Validation"}
          />
        </SpaceBetween>
      ),
    },
  ],
};

const DocumentsListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default DocumentsListing;
