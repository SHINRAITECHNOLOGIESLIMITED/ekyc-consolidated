"use client";

import { Details, DetailsProps } from "@/components/Details";
import { fetchBackGroundCheck } from "@/services/DataService";
import { BackGroundCheck } from "@/types/models";
import { Alert } from "@cloudscape-design/components";
import { useParams } from "next/navigation";
import React from "react";
import BackGroundCheckDetails from "../BackGroundCheckDetails";

const DocumentDetailsPageBackGroundCheck: React.FC = () => {
  const params = useParams();
  const backGroundCheckId = Array.isArray(params.backGroundCheckId)
    ? params.backGroundCheckId[0]
    : params.backGroundCheckId;

  if (!backGroundCheckId) {
    return (
      <Alert type="error" header="Error" dismissible={false}>
        DocumentId not specified
      </Alert>
    );
  }
  const detailsParams: DetailsProps<BackGroundCheck> = {
    title: "BackGroundCheck",
    primaryKey: backGroundCheckId,
    fetcher: (backGroundCheckId: string) => fetchBackGroundCheck(backGroundCheckId),
    itemDetails: BackGroundCheckDetails,
  };

  return <Details {...detailsParams} />;
};

export default DocumentDetailsPageBackGroundCheck;
