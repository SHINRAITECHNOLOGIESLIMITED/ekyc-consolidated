"use client";

import Listing, { ListingProps } from "@/components/Listing";
import { fetchDocumentValidations } from "@/services/DataService";
import type { DocumentValidation } from "@/types/models";
import ValidationDetails from "./[validationId]/ValidationDetails";

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
};

const DocumentsListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default DocumentsListing;
