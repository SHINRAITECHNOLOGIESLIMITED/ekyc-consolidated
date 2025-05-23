"use client";

import { Details, DetailsProps } from "@/components/Details";
import { fetchDocumentVerification } from "@/services/DataService";
import { DocumentVerification } from "@/types/models";
import { Alert } from "@cloudscape-design/components";
import { useParams } from "next/navigation";
import React from "react";
import VerificationDetails from "./VerificationDetails";

const DocumentDetailsPageVerification: React.FC = () => {
  const params = useParams();
  const verificationId = Array.isArray(params.verificationId)
    ? params.verificationId[0]
    : params.verificationId;

  if (!verificationId) {
    return (
      <Alert type="error" header="Error" dismissible={false}>
        DocumentId not specified
      </Alert>
    );
  }
  const detailsParams: DetailsProps<DocumentVerification> = {
    title: "Verification",
    primaryKey: verificationId,
    fetcher: (VerificationId: string) =>
      fetchDocumentVerification(VerificationId),
    itemDetails: VerificationDetails,
  };

  return <Details {...detailsParams} />;
};

export default DocumentDetailsPageVerification;
