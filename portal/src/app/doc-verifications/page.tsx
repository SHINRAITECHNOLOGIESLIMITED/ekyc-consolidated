"use client";

import Listing, { ListingProps } from "@/components/Listing";
import NotImplemented from "@/components/NotImplemented";
import { fetchDocumentVerifications } from "@/services/DataService";
import type { DocumentVerification } from "@/types/models";
import { SpaceBetween } from "@cloudscape-design/components";
import VerificationDetails from "./VerificationDetails";
import { formatPercentage } from "@/utils/formatters";

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
    cell: (item: DocumentVerification) => formatPercentage(item.processing_accuracy),
  },
  {
    id: "accuracy",
    header: "Validity",
    cell: (item: DocumentVerification) => formatPercentage(item.validation_accuracy),
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
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented title={"NationalID Verification"} />
        </SpaceBetween>
      ),
    },
    {
      label: "New Passport Verification",
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented title={"Passport Verification"} />
        </SpaceBetween>
      ),
    },
    {
      label: "New KRAPinCertificate Verification",
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented title={"KRAPinCertificate Verification"} />
        </SpaceBetween>
      ),
    },
  ],
};

const DocumentsListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default DocumentsListing;
