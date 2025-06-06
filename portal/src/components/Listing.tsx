"use client";

import { useCollection } from "@cloudscape-design/collection-hooks";
import {
  Alert,
  Box,
  Button,
  ButtonDropdown,
  Header,
  Modal,
  Pagination,
  SpaceBetween,
  StatusIndicator,
  Table,
  TableProps,
  TextFilter,
} from "@cloudscape-design/components";
import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useState } from "react";

interface EmptyStateProps {
  title: string;
  subtitle: string;
  action: React.ReactNode;
}

export interface ActionProps {
  id: string;
  label: string;
  iconName?: string;
  render: () => React.ReactNode;
}

export interface ListingProps<T> {
  title: string;
  getAll: () => Promise<ReadonlyArray<T>>;
  pageSize: number;
  columnDefinitions: readonly TableProps.ColumnDefinition<T>[];
  itemKey: (item: T) => string;
  itemDetailsLink?: (item: T) => string;
  renderItemDetails?: (item: T) => React.ReactNode;
  actions?: ActionProps[];
}

export function getMatchesCountText(count: number | undefined) {
  return count === 1 ? `1 match` : `${count} matches`;
}

const paginationLabels = {
  nextPageLabel: "Next page",
  pageLabel: (pageNumber: number) => `Page ${pageNumber} of all pages`,
  previousPageLabel: "Previous page",
};

function EmptyState({ title, subtitle, action }: EmptyStateProps) {
  return (
    <Box textAlign="center" color="inherit">
      <Box variant="strong" textAlign="center" color="inherit">
        {title}
      </Box>
      <Box variant="p" padding={{ bottom: "s" }} color="inherit">
        {subtitle}
      </Box>
      {action}
    </Box>
  );
}

// Create a type-safe cache outside the component to persist across re-renders
const dataCache = new Map<string, ReadonlyArray<unknown>>();

export const Listing = <T,>({
  title,
  getAll,
  pageSize,
  columnDefinitions,
  itemKey,
  itemDetailsLink,
  renderItemDetails,
  actions,
}: ListingProps<T>) => {
  const router = useRouter();
  const cacheKey = title; // Using title as cache key, you might want to use a more unique identifier

  const [allItems, setAllItems] = useState<ReadonlyArray<T>>(() => {
    // Initialize state with cached data if available
    return (dataCache.get(cacheKey) as ReadonlyArray<T>) || [];
  });
  const [loading, setLoading] = useState(!dataCache.has(cacheKey));
  const [error, setError] = useState<string | null>(null);
  const [modal, setModal] = useState<React.ReactNode | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);

  const fetchItems = useCallback(
    async (forceRefresh: boolean = false) => {
      // If data is cached and not forcing refresh, use cached data
      if (!forceRefresh && dataCache.has(cacheKey)) {
        setAllItems((dataCache.get(cacheKey) as ReadonlyArray<T>) || []);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const data = await getAll();
        setAllItems(data);
        // Update cache
        dataCache.set(cacheKey, data);
        setError(null);
      } catch (err) {
        setError(`Failed to fetch ${title}: ${err}`);
      } finally {
        setLoading(false);
      }
    },
    [getAll, title, cacheKey]
  );

  useEffect(() => {
    fetchItems(false);
  }, [fetchItems]);

  const handleRefresh = () => {
    fetchItems(true);
  };

  const {
    items,
    actions: collectionActions,
    filteredItemsCount,
    collectionProps,
    filterProps,
    paginationProps,
  } = useCollection(allItems, {
    filtering: {
      empty: (
        <EmptyState
          title={`No ${title}`}
          subtitle={`No ${title} found in the backend`}
          action={<Button onClick={handleRefresh}>Refresh</Button>}
        />
      ),
      noMatch: (
        <EmptyState
          title={`No ${title}`}
          subtitle={`No ${title} found that match the criteria`}
          action={
            <Button onClick={() => collectionActions.setFiltering("")}>
              Clear filter
            </Button>
          }
        />
      ),
    },
    pagination: { pageSize },
    sorting: {},
    selection: {
      trackBy: itemKey,
    },
  });

  const { selectedItems = [] } = collectionProps;

  if (itemDetailsLink && !renderItemDetails) {
    const actionColumn: TableProps.ColumnDefinition<T> = {
      id: "actions",
      header: "Details",
      cell: (item) => (
        <Button
          variant="normal"
          iconName="arrow-right"
          onClick={(e) => {
            e.stopPropagation();
            router.push(itemDetailsLink(item));
          }}
        ></Button>
      ),
      width: 100,
    };
    columnDefinitions = [...columnDefinitions, actionColumn];
  }

  if (loading)
    return <StatusIndicator type="loading">Loading {title}...</StatusIndicator>;

  if (error)
    return (
      <Alert type="error" header="Error" dismissible={false}>
        {error}
      </Alert>
    );
  const action_items = actions?.map((action, index) => ({
                      id: index.toString(),
                      text: action.label
                    })) ?? [];
  return (
    <>
      <Table
        {...collectionProps}
        variant="full-page"
        header={
          <Header
            counter={
              selectedItems.length
                ? `(${selectedItems.length}/${allItems.length})`
                : `(${allItems.length})`
            }
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                {actions && actions.length > 0 && (
                  <ButtonDropdown
                    items={action_items}
                    onItemClick={({ detail }) => {
                      const actionIndex = parseInt(detail.id);
                      const action = actions[actionIndex];
                      if (action && action.render) {
                        setModal(action.render());
                        setIsModalVisible(true);
                      }
                    }}
                  >
                    Actions
                  </ButtonDropdown>
                )}
                <Button
                  iconName="refresh"
                  loading={loading}
                  onClick={handleRefresh}
                >
                  Refresh
                </Button>
              </SpaceBetween>
            }
          >
            {title}
          </Header>
        }
        columnDefinitions={columnDefinitions}
        items={items}
        pagination={
          <Pagination {...paginationProps} ariaLabels={paginationLabels} />
        }
        stripedRows
        stickyHeader
        loading={loading}
        trackBy={itemKey}
        loadingText={`Loading ${title}...`}
        filter={
          <TextFilter
            {...filterProps}
            countText={getMatchesCountText(filteredItemsCount)}
            filteringAriaLabel="Filter instances"
          />
        }
        onRowClick={
          renderItemDetails
            ? ({ detail }) => {
                if (detail.item) {
                  setModal(renderItemDetails(detail.item as T));
                  setIsModalVisible(true);
                }
              }
            : undefined
        }
      />

      {modal && (
        <Modal
          visible={isModalVisible}
          onDismiss={() => setIsModalVisible(false)}
          size="large"
        >
          {modal}
        </Modal>
      )}
    </>
  );
};

export default Listing;
