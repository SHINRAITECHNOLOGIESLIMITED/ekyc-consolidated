"use client";

import Listing, { ListingProps } from "@/components/Listing";
import { fetchBackGroundChecks } from "@/services/DataService";
import type { BackGroundCheck } from "@/types/models";
import BackGroundCheckDetails from "./BackGroundCheckDetails";
import DocumentForm from "@/components/DocumentForm";

const columnDefinitions = [
  {
    id: "backGroundCheckId",
    header: "Check ID",
    cell: (item: BackGroundCheck) => item.backGroundCheckId,
  },
  {
    id: "firstName",
    header: "First Name",
    cell: (item: BackGroundCheck) => item.firstName,
  },
  {
    id: "middleName",
    header: "MiddleName",
    cell: (item: BackGroundCheck) => item.middleName ?? "",
  },
  {
    id: "lastName",
    header: "Last Name",
    cell: (item: BackGroundCheck) => item.lastName,
  },
  {
    id: "gender",
    header: "gender",
    cell: (item: BackGroundCheck) => item.gender,
  },
  {
    id: "dob",
    header: "Date Of birth",
    cell: (item: BackGroundCheck) => item.dob,
  },
  {
    id: "nationalIdentificationNumber",
    header: "ID Number",
    cell: (item: BackGroundCheck) => item.nationalIdentificationNumber,
  },
  {
    id: "countryCode",
    header: "Country Code",
    cell: (item: BackGroundCheck) => item.countryCode,
  },
  {
    id: "entityType",
    header: "Entity Type",
    cell: (item: BackGroundCheck) => item.entityType,
  },
  {
    id: "sourceName",
    header: "Source Name",
    cell: (item: BackGroundCheck) => item.sourceName,
  },
];

const listingProps: ListingProps<BackGroundCheck> = {
  title: "BackGround Checks",
  getAll: fetchBackGroundChecks,
  pageSize: 100,
  columnDefinitions,
  itemKey: (item: BackGroundCheck) => item.backGroundCheckId.toString(),
  itemDetailsLink: (item: BackGroundCheck) =>
    `background-checks/${item.backGroundCheckId}`,
  renderItemDetails: (item: BackGroundCheck) => BackGroundCheckDetails(item),
  actions: [
    {
      label: "New NationalId Verification",
      id: "nationalid",
      render: () => {
        return <BackGroundCheckForm />;
      },
    },
  ],
};

const BackGroundCheckForm: React.FC = () => (
  <DocumentForm
    title="Background Check"
    apiEndpoint="backgroundcheck"
    fields={[
      { id: "firstName", label: "First Name", type: "text", required: true, placeholder: "Jane" },
      { id: "middleName", label: "Middle Name", type: "text", placeholder: "Wairimu" },
      { id: "lastName", label: "Last Name", type: "text", required: true, placeholder: "Maina" },
      { id: "gender", label: "Gender", type: "text", required: true, placeholder: "Female" },
      { id: "dateOfBirth", label: "Date of Birth", type: "date", required: true, placeholder: "1985-01-01" },
      { id: "nationalIdentificationNumber", label: "ID Number", type: "text", required: true, placeholder: "23667272" },
    ]}
  />
);

const BackGroundChecksListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default BackGroundChecksListing;
