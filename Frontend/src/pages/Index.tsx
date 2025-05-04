
import React, { useState } from "react";
import Layout from "@/components/layout/Layout";
import CommandInput from "@/components/dashboard/CommandInput";
import InterpretationDisplay, { InterpretationData } from "@/components/dashboard/InterpretationDisplay";
import WalletCard from "@/components/wallet/WalletCard";
import TransactionList, { Transaction } from "@/components/transactions/TransactionList";

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

const Index = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [interpretation, setInterpretation] = useState<InterpretationData | null>(null);

  const handleCommandSubmit = (command: string) => {
    setIsProcessing(true);
    
    // Simulate AI processing delay
    setTimeout(() => {
      // Basic parsing logic (in a real app, this would be done by the AI)
      let mockInterpretation: InterpretationData;
      
      if (command.toLowerCase().includes("send") && command.toLowerCase().includes("algo")) {
        // Parse send commands
        const amountMatch = command.match(/\d+(\.\d+)?\s*algo/i);
        const addressMatch = command.match(/to\s+([A-Za-z0-9]+)/i);
        
        mockInterpretation = {
          type: "send",
          details: {
            amount: amountMatch ? amountMatch[0].replace(/algo/i, "").trim() : "0",
            recipient: addressMatch ? addressMatch[1] : "XY3Z...AB45",
          },
          rawCommand: command,
        };
      } else if (command.toLowerCase().includes("mint") && command.toLowerCase().includes("nft")) {
        // Parse mint commands
        const nameMatch = command.match(/named\s+['""]([^'""]+)['"]/i) || 
                         command.match(/mint\s+['""]([^'""]+)['"]/i);
        const descMatch = command.match(/description\s+['""]([^'""]+)['"]/i) || 
                          command.match(/with\s+['""]([^'""]+)['"]/i);
        
        mockInterpretation = {
          type: "mint",
          details: {
            name: nameMatch ? nameMatch[1] : "Untitled NFT",
            description: descMatch ? descMatch[1] : "No description provided",
            imageUrl: "https://images.unsplash.com/photo-1487058792275-0ad4aaf24ca7",
          },
          rawCommand: command,
        };
      } else {
        // Default to a send transaction if parsing fails
        mockInterpretation = {
          type: "send",
          details: {
            amount: "1",
            recipient: "Address not recognized",
          },
          rawCommand: command,
        };
      }
      
      setInterpretation(mockInterpretation);
      setIsProcessing(false);
    }, 1500);
  };

  const handleConfirm = () => {
    setIsProcessing(true);
    
    // Simulate transaction processing
    setTimeout(() => {
      setIsProcessing(false);
      setInterpretation(null);
      // In a real app, this would trigger the actual transaction
    }, 2000);
  };

  const handleCancel = () => {
    setInterpretation(null);
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8 md:py-12">
        <div className="mb-8 text-center">
          <h1 className="text-3xl md:text-4xl font-bold mb-2 algo-text-gradient">
            Algo-Intent
          </h1>
          <p className="text-lg text-muted-foreground">
            Execute Algorand transactions with natural language
          </p>
        </div>

        <div className="mx-auto max-w-3xl mb-12">
          <CommandInput 
            onSubmit={handleCommandSubmit} 
            isProcessing={isProcessing} 
          />
          
          {isProcessing && !interpretation && (
            <div className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center">
                <div className="size-5 rounded-full animate-pulse algo-gradient mb-4"></div>
                <p className="text-sm text-muted-foreground">Processing your command...</p>
              </div>
            </div>
          )}
          
          {interpretation && (
            <div className="mt-4">
              <InterpretationDisplay 
                interpretation={interpretation}
                onConfirm={handleConfirm}
                onCancel={handleCancel}
              />
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <WalletCard 
              address="ABC123XYZ456789DEFGHI000111222333"
              balance="100.57"
            />
          </div>
          <div className="md:col-span-2">
            <TransactionList transactions={mockTransactions} />
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Index;
