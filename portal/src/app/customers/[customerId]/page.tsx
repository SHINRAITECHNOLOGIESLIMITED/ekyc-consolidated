"use client";

import { Details, DetailsProps } from "@/components/Details";
import { fetchCustomer } from "@/services/DataService";
import { Customer } from "@/types/models";
import { Alert } from "@cloudscape-design/components";
import { useParams } from "next/navigation";
import React from "react";
import CustomerDetails from "../CustomerDetails";

const CustomerDetailsPage: React.FC = () => {
  const params = useParams();
  const customerId = Array.isArray(params.customerId)
    ? params.customerId[0]
    : params.customerId;

  if (!customerId) {
    return (
      <Alert type="error" header="Error" dismissible={false}>
        DocumentId not specified
      </Alert>
    );
  }
  const detailsParams: DetailsProps<Customer> = {
    title: "Customer",
    primaryKey: customerId,
    fetcher: (customerId: string) => fetchCustomer(customerId),
    itemDetails: CustomerDetails,
  };

  return <Details {...detailsParams} />;
};

export default CustomerDetailsPage;
