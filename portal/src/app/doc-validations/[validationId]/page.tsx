"use client";

import { Details, DetailsProps } from "@/components/Details";
import { fetchDocumentValidation } from "@/services/DataService";
import { DocumentValidation } from "@/types/models";
import { Alert } from "@cloudscape-design/components";
import { useParams } from "next/navigation";
import React from "react";
import ValidationDetails from "../ValidationDetails";

const DocumentDetailsPageValidation: React.FC = () => {
  const params = useParams();
  const validationId = Array.isArray(params.validationId)
    ? params.validationId[0]
    : params.validationId;

  if (!validationId) {
    return (
      <Alert type="error" header="Error" dismissible={false}>
        DocumentId not specified
      </Alert>
    );
  }
  const detailsParams: DetailsProps<DocumentValidation> = {
    title: "Validation",
    primaryKey: validationId,
    fetcher: (validationId: string) => fetchDocumentValidation(validationId),
    itemDetails: ValidationDetails,
  };

  return <Details {...detailsParams} />;
};

export default DocumentDetailsPageValidation;
