
import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface InterpretationData {
  type: "send" | "mint";
  details: {
    amount?: string;
    recipient?: string;
    name?: string;
    description?: string;
    imageUrl?: string;
  };
  rawCommand: string;
}

interface InterpretationDisplayProps {
  interpretation: InterpretationData | null;
  onConfirm: () => void;
  onCancel: () => void;
  className?: string;
}

const InterpretationDisplay: React.FC<InterpretationDisplayProps> = ({
  interpretation,
  onConfirm,
  onCancel,
  className,
}) => {
  if (!interpretation) return null;

  return (
    <Card className={cn("w-full overflow-hidden animate-fade-in", className)}>
      <div className="py-2 px-4 border-b bg-muted/50">
        <h3 className="text-sm font-medium">AI Interpretation</h3>
      </div>
      <CardContent className="py-4">
        <div className="space-y-4">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Original Command</p>
            <p className="text-sm font-medium">{interpretation.rawCommand}</p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground mb-1">Interpreted Action</p>
            <p className="text-sm font-medium">
              {interpretation.type === "send"
                ? "Send ALGO Tokens"
                : "Mint NFT Asset"}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {interpretation.type === "send" ? (
              <>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Amount</p>
                  <p className="text-sm font-medium">{interpretation.details.amount} ALGO</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Recipient Address</p>
                  <p className="text-sm font-medium break-all">{interpretation.details.recipient}</p>
                </div>
              </>
            ) : (
              <>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">NFT Name</p>
                  <p className="text-sm font-medium">{interpretation.details.name}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Description</p>
                  <p className="text-sm font-medium">{interpretation.details.description}</p>
                </div>
                {interpretation.details.imageUrl && (
                  <div className="col-span-1 md:col-span-2">
                    <p className="text-xs text-muted-foreground mb-1">Preview</p>
                    <img 
                      src={interpretation.details.imageUrl} 
                      alt="NFT Preview" 
                      className="w-20 h-20 object-cover rounded-md" 
                    />
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-end gap-2 py-3 px-4 bg-muted/30 border-t">
        <Button
          variant="outline"
          size="sm"
          className="gap-1"
          onClick={onCancel}
        >
          <X className="size-4" /> Cancel
        </Button>
        <Button
          size="sm"
          className="gap-1"
          onClick={onConfirm}
        >
          <Check className="size-4" /> Confirm
        </Button>
      </CardFooter>
    </Card>
  );
};

export default InterpretationDisplay;
