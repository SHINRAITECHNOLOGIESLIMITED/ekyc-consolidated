"use client";

import Listing, { ListingProps } from "@/components/Listing";
import NotImplemented from "@/components/NotImplemented";
import { fetchBackGroundChecks } from "@/services/DataService";
import type { BackGroundCheck } from "@/types/models";
import { SpaceBetween } from "@cloudscape-design/components";
import BackGroundCheckDetails from "./BackGroundCheckDetails";

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
      id: "background-check",
      label: "New BackGround Check",
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented title={"Background Check"} />
        </SpaceBetween>
      ),
    },
  ],
};

const BackGroundChecksListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default BackGroundChecksListing;
