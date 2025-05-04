
import React from "react";
import Layout from "@/components/layout/Layout";
import TransactionList, { Transaction } from "@/components/transactions/TransactionList";

// Mock data for transactions
const mockTransactions: Transaction[] = [
  {
    id: "1",
    type: "send",
    amount: "10.5",
    recipient: "XY3Z...AB45",
    date: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
    status: "confirmed",
  },
  {
    id: "2",
    type: "receive",
    amount: "25",
    sender: "AB12...TR34",
    date: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
    status: "confirmed",
  },
  {
    id: "3",
    type: "mint",
    assetName: "Digital Artwork #1",
    date: new Date(Date.now() - 1000 * 60 * 60 * 48), // 2 days ago
    status: "confirmed",
  },
  {
    id: "4",
    type: "send",
    amount: "5",
    recipient: "DF12...XY78",
    date: new Date(Date.now() - 1000 * 60 * 60 * 72), // 3 days ago
    status: "failed",
  },
  {
    id: "5",
    type: "receive",
    amount: "2.75",
    sender: "JK90...PQ12",
    date: new Date(Date.now() - 1000 * 60 * 60 * 100), // ~4 days ago
    status: "confirmed",
  },
];

const Transactions = () => {
  return (
    <Layout>
      <div className="container mx-auto px-4 py-8 md:py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-2">Transaction History</h1>
          <p className="text-muted-foreground">View and filter your transaction history</p>
        </div>

        <div className="mb-6">
          {/* Filter options can be added here in the future */}
        </div>

        <TransactionList transactions={mockTransactions} />
      </div>
    </Layout>
  );
};

export default Transactions;
