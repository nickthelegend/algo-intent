
import React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface Transaction {
  id: string;
  type: "send" | "receive" | "mint";
  amount?: string;
  recipient?: string;
  sender?: string;
  assetName?: string;
  date: Date;
  status: "confirmed" | "pending" | "failed";
}

interface TransactionListProps {
  transactions: Transaction[];
  className?: string;
}

const TransactionList: React.FC<TransactionListProps> = ({
  transactions,
  className,
}) => {
  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="px-4 py-3 border-b">
        <h3 className="text-base font-medium">Recent Transactions</h3>
      </CardHeader>
      <CardContent className="p-0">
        {transactions.length === 0 ? (
          <div className="flex items-center justify-center py-8 px-4 text-center">
            <div>
              <p className="text-sm text-muted-foreground">No transactions yet</p>
              <p className="text-xs mt-1 text-muted-foreground">
                Your transaction history will appear here
              </p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((tx) => (
                  <TableRow key={tx.id}>
                    <TableCell>
                      <Badge
                        variant={
                          tx.type === "send"
                            ? "outline"
                            : tx.type === "receive"
                            ? "secondary"
                            : "default"
                        }
                      >
                        {tx.type === "send"
                          ? "Sent"
                          : tx.type === "receive"
                          ? "Received"
                          : "Mint NFT"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        {(tx.type === "send" || tx.type === "receive") && (
                          <>
                            <span className="text-sm font-medium">
                              {tx.amount} ALGO
                            </span>
                            <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                              {tx.type === "send" 
                                ? `To: ${tx.recipient}` 
                                : `From: ${tx.sender}`}
                            </span>
                          </>
                        )}
                        {tx.type === "mint" && (
                          <>
                            <span className="text-sm font-medium">
                              {tx.assetName}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              NFT Minted
                            </span>
                          </>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">
                        {tx.date.toLocaleDateString()}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          tx.status === "confirmed"
                            ? "default"
                            : tx.status === "pending"
                            ? "outline"
                            : "destructive"
                        }
                      >
                        {tx.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TransactionList;
