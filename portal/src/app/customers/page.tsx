"use client";

import Listing, { ListingProps } from "@/components/Listing";
import { fetchCustomers } from "@/services/DataService";
import type { Customer } from "@/types/models";
import CustomerDetails from "./CustomerDetails";
import DocumentForm from "@/components/DocumentForm";

const columnDefinitions = [
  {
    id: "customerId",
    header: "Customer ID",
    cell: (item: Customer) => item.customerId,
  },
  {
    id: "name",
    header: "Name",
    cell: (item: Customer) => item.name,
  },
  {
    id: "pinNumber",
    header: "PIN Number",
    cell: (item: Customer) => item.pinNumber,
  },
  {
    id: "idNumber",
    header: "ID Number",
    cell: (item: Customer) => item.idNumber,
  },
  {
    id: "gender",
    header: "Gender",
    cell: (item: Customer) => item.gender,
  },
  {
    id: "dateOfBirth",
    header: "Date of Birth",
    cell: (item: Customer) => item.dateOfBirth,
  },
  {
    id: "kycStatus",
    header: "KYC Status",
    cell: (item: Customer) => item.kycStatus,
  },
   {
    id: "kycCertificate",
    header: "KYC Certificate",
    cell: (item: Customer) => item.kycCertificateS3Path
  },
];

const listingProps: ListingProps<Customer> = {
  title: "Customers",
  getAll: fetchCustomers,
  pageSize: 100,
  columnDefinitions,
  itemKey: (item: Customer) => item.customerId.toString(),
  itemDetailsLink: (item: Customer) => `customers/${item.customerId}`,
  renderItemDetails: (item: Customer) => CustomerDetails(item),
  actions: [
    {
      id: "customer-reg",
      label: "New Customer",
      render: () => {
        return <CustomerForm />;
      },
    }
  ],
};

const CustomerForm: React.FC = () => (
  <DocumentForm
    title="Customer Registration"
    apiEndpoint="customer-registration"
    fields={[
      { id: "name", label: "Full Name", type: "text", required: true, placeholder: "Jane Wairimu Maina" },
      { id: "pinNumber", label: "PIN Number", type: "text", required: true, placeholder: "A003388522V" },
      { id: "idNumber", label: "ID Number", type: "text", required: true, placeholder: "23667272" },
      { id: "passportNumber", label: "Passport Number", type: "text", placeholder: "BK120129" },
      { id: "gender", label: "Gender", type: "text", required: true, placeholder: "Female" },
      { id: "dateOfBirth", label: "Date of Birth", type: "date", required: true, placeholder: "1985-01-01" },
      { id: "passportPhotoUrl", label: "Passport Photo", type: "document", required: true, acceptedFileTypes: [".jpg", ".jpeg", ".png"] },
      { id: "nationalIdCardUrl", label: "National ID Card", type: "document", required: true, acceptedFileTypes: [".jpg", ".jpeg", ".png", ".pdf"] },
      { id: "passportUrl", label: "Passport Scan", type: "document", acceptedFileTypes: [".jpg", ".jpeg", ".png", ".pdf"] },
      { id: "kraPinCardUrl", label: "KRA PIN Certificate", type: "document", required: true, acceptedFileTypes: [".jpg", ".jpeg", ".png", ".pdf"] },
    ]}
  />
);

const CustomersListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default CustomersListing;
