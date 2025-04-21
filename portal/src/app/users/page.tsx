"use client";

import Listing, {ListingProps} from '@/components/Listing';
import {fetchUsers} from '@/services/DataService';
import {CognitoUser} from "@/types/interfaces";


const columnDefinitions =
    [
        {
            id: "username",
            header: "User Name",
            cell: (item: CognitoUser) => item.username
        },
        {
            id: "email",
            header: "Email",
            cell: (item: CognitoUser) => item.email || "-"
        },
        {
            id: "Status",
            header: "Status",
            cell: (item: CognitoUser) => item.userStatus
        },
        {
            id: "Enabled",
            header: "Enabled",
            cell: (item: CognitoUser) => item.enabled ? "Yes" : "No"
        }
    ];


const listingProps: ListingProps<CognitoUser> = {
    title: "Users",
    getAll: fetchUsers,
    pageSize: 100,
    columnDefinitions,
    itemKey: (item: CognitoUser) => item.username.toString()
};

const UsersListing: React.FC = () => {
    return <Listing {...listingProps} />;
};

export default UsersListing;
