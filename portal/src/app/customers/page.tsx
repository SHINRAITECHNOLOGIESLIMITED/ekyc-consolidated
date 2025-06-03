"use client";

import Listing, { ListingProps } from "@/components/Listing";
import NotImplemented from "@/components/NotImplemented";
import { fetchCustomers } from "@/services/DataService";
import type { Customer } from "@/types/models";
import { SpaceBetween } from "@cloudscape-design/components";
import CustomerDetails from "./CustomerDetails";

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
      label: "New Customer",
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented title={"Customer Registration"} />
        </SpaceBetween>
      ),
    },
  ],
};

const CustomersListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default CustomersListing;
