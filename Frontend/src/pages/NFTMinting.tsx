
import React, { useState } from "react";
import Layout from "@/components/layout/Layout";
import NFTMintingForm from "@/components/nft/NFTMintingForm";
import { useToast } from "@/hooks/use-toast";

const NFTMinting = () => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleMintNFT = (data: {
    name: string;
    description: string;
    image: File | null;
  }) => {
    setIsSubmitting(true);
    
    // Simulate minting process
    setTimeout(() => {
      toast({
        title: "NFT Minted Successfully",
        description: `Your NFT "${data.name}" has been minted to the Algorand TestNet.`,
      });
      setIsSubmitting(false);
    }, 2000);
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8 md:py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-2">NFT Minting</h1>
          <p className="text-muted-foreground">Create and mint your NFTs on Algorand TestNet</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-8">
            <NFTMintingForm onSubmit={handleMintNFT} isSubmitting={isSubmitting} />
          </div>
          <div className="md:col-span-4">
            <div className="glass-card rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">About NFT Minting</h3>
              <div className="space-y-4 text-sm">
                <p>
                  Minting an NFT creates a unique digital asset on the Algorand
                  blockchain that can't be replicated or forged.
                </p>
                <p>
                  Each NFT you mint will be assigned a unique Asset ID and will
                  be visible in your wallet after minting.
                </p>
                <p>
                  On the TestNet, minting is free and uses test ALGO tokens. On
                  MainNet, a small fee would be required.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default NFTMinting;
