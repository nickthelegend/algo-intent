
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

interface NFTMintingFormProps {
  onSubmit: (data: {
    name: string;
    description: string;
    image: File | null;
    properties?: Record<string, string>;
  }) => void;
  isSubmitting?: boolean;
  className?: string;
}

const NFTMintingForm: React.FC<NFTMintingFormProps> = ({
  onSubmit,
  isSubmitting = false,
  className,
}) => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  
  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onload = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      description,
      image,
    });
  };
  
  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="px-6 py-4 border-b">
        <h3 className="text-lg font-medium">Mint New NFT</h3>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="p-6">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="nft-name">NFT Name</Label>
                <Input
                  id="nft-name"
                  placeholder="Enter NFT name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              
              <div>
                <div className="space-y-2">
                  <Label htmlFor="nft-image">Upload Image</Label>
                  <div className="border-2 border-dashed rounded-lg p-4 cursor-pointer hover:bg-muted/50 transition-colors relative">
                    <input
                      id="nft-image"
                      type="file"
                      accept="image/*"
                      onChange={handleImageChange}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    {imagePreview ? (
                      <div className="flex items-center justify-center">
                        <img
                          src={imagePreview}
                          alt="NFT Preview"
                          className="max-h-[120px] max-w-full rounded"
                        />
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-4">
                        <Upload className="size-8 mb-2 text-muted-foreground" />
                        <p className="text-sm text-muted-foreground">
                          Click or drop image here
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          PNG, JPG, GIF (max 5MB)
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="nft-description">Description</Label>
              <Textarea
                id="nft-description"
                placeholder="Enter a description for your NFT"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
              />
            </div>
          </div>
        </CardContent>
        
        <CardFooter className="flex justify-end p-6 gap-3 border-t bg-muted/20">
          <Button 
            type="reset" 
            variant="outline"
            onClick={() => {
              setName("");
              setDescription("");
              setImage(null);
              setImagePreview(null);
            }}
            disabled={isSubmitting}
          >
            Reset
          </Button>
          <Button type="submit" disabled={!name || isSubmitting}>
            {isSubmitting ? "Processing..." : "Mint NFT"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
};

export default NFTMintingForm;
