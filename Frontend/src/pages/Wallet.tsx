
import React, { useState } from "react";
import Layout from "@/components/layout/Layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import WalletCard from "@/components/wallet/WalletCard";
import TransactionList, { Transaction } from "@/components/transactions/TransactionList";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

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
];

const Wallet = () => {
  const [hasWallet, setHasWallet] = useState(true);
  const [isCreatingWallet, setIsCreatingWallet] = useState(false);

  const handleCreateWallet = (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreatingWallet(true);
    
    // Simulate wallet creation
    setTimeout(() => {
      setHasWallet(true);
      setIsCreatingWallet(false);
    }, 1500);
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8 md:py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-2">Wallet Management</h1>
          <p className="text-muted-foreground">Manage your Algorand TestNet wallet</p>
        </div>

        {!hasWallet ? (
          <div className="max-w-md mx-auto">
            <Card>
              <CardHeader className="text-center">
                <h2 className="text-2xl font-semibold">Create New Wallet</h2>
                <p className="text-sm text-muted-foreground">
                  Set up your TestNet wallet to start transacting on Algorand
                </p>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateWallet}>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="password">Secure Password</Label>
                      <Input
                        id="password"
                        type="password"
                        placeholder="Enter a secure password"
                        required
                      />
                      <p className="text-xs text-muted-foreground">
                        This password will be used to encrypt your wallet
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="confirm-password">Confirm Password</Label>
                      <Input
                        id="confirm-password"
                        type="password"
                        placeholder="Confirm your password"
                        required
                      />
                    </div>
                    
                    <div className="pt-2">
                      <Button type="submit" className="w-full" disabled={isCreatingWallet}>
                        {isCreatingWallet ? "Creating..." : "Create Wallet"}
                      </Button>
                    </div>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            <div className="md:col-span-4">
              <WalletCard 
                address="ABC123XYZ456789DEFGHI000111222333"
                balance="100.57"
              />
              
              <Card className="mt-6">
                <CardHeader className="px-4 py-3 border-b">
                  <h3 className="font-medium">Wallet Actions</h3>
                </CardHeader>
                <CardContent className="p-4 space-y-3">
                  <Button variant="outline" className="w-full justify-start">Fund with TestNet ALGO</Button>
                  <Button variant="outline" className="w-full justify-start">Export Wallet</Button>
                  <Button variant="outline" className="w-full justify-start">Backup Recovery Phrase</Button>
                </CardContent>
              </Card>
            </div>
            
            <div className="md:col-span-8">
              <Tabs defaultValue="transactions">
                <TabsList className="grid grid-cols-2 mb-6">
                  <TabsTrigger value="transactions">Transactions</TabsTrigger>
                  <TabsTrigger value="assets">Assets</TabsTrigger>
                </TabsList>
                <TabsContent value="transactions" className={cn("animate-fade-in")}>
                  <TransactionList transactions={mockTransactions} />
                </TabsContent>
                <TabsContent value="assets" className={cn("animate-fade-in")}>
                  <Card>
                    <CardHeader className="px-4 py-3 border-b">
                      <h3 className="font-medium">Your Assets</h3>
                    </CardHeader>
                    <CardContent className="p-6">
                      <div className="text-center py-8">
                        <p className="text-muted-foreground">No assets found in this wallet</p>
                        <p className="text-sm text-muted-foreground mt-1">Mint your first NFT to see it here</p>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Wallet;
