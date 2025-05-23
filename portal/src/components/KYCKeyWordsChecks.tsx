import {
  Box,
  Container,
  Header,
  StatusIndicator,
  Table,
} from "@cloudscape-design/components";
import React from "react";

export interface KeyWordCheck {
  check: string;
  result: boolean;
}

export interface KeyWordChecks {
  [key: string]: KeyWordCheck;
}

interface KYCKeyWordsChecksProps {
  results: KeyWordChecks;
}

const KYCKeyWordsChecks: React.FC<KYCKeyWordsChecksProps> = ({
  results,
}) => {
  console.log(results);
  const items = Object.entries(results || {}).map(([index, result]) => {
    console.log(index, result);
    const item = {
      check: result.check.replace(/([A-Z])/g, " $1").trim(),
      result: result.result
    };
    console.log(item);
    return item;
  });

  return (
    <Container>
      <Header variant="h2">Keywords Checks</Header>
      <Table
        columnDefinitions={[
          {
            id: "field",
            header: "Check",
            cell: (item) => item.check,
          },
          {
            id: "result",
            header: "Result",
            cell: (item) => (
              <StatusIndicator
                type={
                  item.result
                    ? "success"
                    : "error"
                }
              >
                {item.result
                    ? "Present"
                    : "Abscent"}
              </StatusIndicator>
            ),
          },
        ]}
        items={items}
        variant="embedded"
        stripedRows
        empty={
          <Box textAlign="center" color="inherit">
            <b>No keyword checks results available</b>
          </Box>
        }
      />
    </Container>
  );
};

export default KYCKeyWordsChecks;
