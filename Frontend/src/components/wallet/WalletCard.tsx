
import React from "react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy, Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";

interface WalletCardProps {
  address: string;
  balance: string;
  className?: string;
}

const WalletCard: React.FC<WalletCardProps> = ({ address, balance, className }) => {
  const [showAddress, setShowAddress] = React.useState(false);
  
  const toggleAddressVisibility = () => {
    setShowAddress(!showAddress);
  };
  
  const copyAddressToClipboard = () => {
    navigator.clipboard.writeText(address);
    // Could add a toast notification here
  };

  const truncateAddress = (address: string) => {
    return `${address.slice(0, 8)}...${address.slice(-8)}`;
  };

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">My TestNet Wallet</h3>
          <div className="size-8 rounded-full algo-gradient flex items-center justify-center">
            <span className="font-bold text-white text-xs">AG</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4 pt-0">
        <div className="space-y-4">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Wallet Address</p>
            <div className="flex items-center gap-2">
              <p className="font-mono text-sm break-all">
                {showAddress ? address : truncateAddress(address)}
              </p>
              <Button
                variant="ghost"
                size="icon"
                className="size-6 rounded-full"
                onClick={toggleAddressVisibility}
                title={showAddress ? "Hide address" : "Show full address"}
              >
                {showAddress ? (
                  <EyeOff className="size-3.5" />
                ) : (
                  <Eye className="size-3.5" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-6 rounded-full"
                onClick={copyAddressToClipboard}
                title="Copy address to clipboard"
              >
                <Copy className="size-3.5" />
              </Button>
            </div>
          </div>
          
          <div>
            <p className="text-xs text-muted-foreground mb-0.5">Balance</p>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-semibold">{balance}</p>
              <p className="text-sm font-medium">ALGO</p>
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex flex-col gap-2 p-4 border-t bg-muted/20">
        <Button className="w-full" size="sm">
          Send Tokens
        </Button>
      </CardFooter>
    </Card>
  );
};

export default WalletCard;
