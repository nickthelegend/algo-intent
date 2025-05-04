
import React from "react";
import Layout from "@/components/layout/Layout";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const About = () => {
  return (
    <Layout>
      <div className="container mx-auto px-4 py-8 md:py-12">
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-2">About Algo-Intent</h1>
          <p className="text-muted-foreground">Learn about our AI-powered Algorand interface</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 mb-12">
          <div className="md:col-span-7">
            <h2 className="text-2xl font-semibold mb-4">Natural Language Interface for Algorand</h2>
            <div className="space-y-4">
              <p>
                Algo-Intent is a revolutionary platform that combines the power of natural
                language processing with blockchain technology to create a seamless user
                experience for interacting with the Algorand network.
              </p>
              <p>
                Our platform enables users to perform complex blockchain operations using
                simple, conversational commands. Whether you want to send ALGO tokens or mint
                unique NFTs, you can do it all with natural language instructions.
              </p>
              <p>
                Built for both beginners and experienced blockchain users, Algo-Intent
                removes the technical barriers that often prevent wider adoption of
                blockchain technology.
              </p>
            </div>

            <div className="mt-8">
              <h3 className="text-xl font-semibold mb-4">Key Features</h3>
              <ul className="space-y-2">
                <li className="flex gap-2">
                  <div className="size-5 rounded-full algo-gradient flex-shrink-0 mt-1"></div>
                  <div>
                    <span className="font-medium">Natural Language Processing:</span> Type
                    commands in plain English to execute blockchain transactions
                  </div>
                </li>
                <li className="flex gap-2">
                  <div className="size-5 rounded-full algo-gradient flex-shrink-0 mt-1"></div>
                  <div>
                    <span className="font-medium">Secure Wallet Management:</span> Create and
                    manage your Algorand TestNet wallet with password protection
                  </div>
                </li>
                <li className="flex gap-2">
                  <div className="size-5 rounded-full algo-gradient flex-shrink-0 mt-1"></div>
                  <div>
                    <span className="font-medium">Token Transfers:</span> Send and receive
                    ALGO tokens with simple commands
                  </div>
                </li>
                <li className="flex gap-2">
                  <div className="size-5 rounded-full algo-gradient flex-shrink-0 mt-1"></div>
                  <div>
                    <span className="font-medium">NFT Creation:</span> Mint unique NFTs with
                    customizable properties and metadata
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <div className="md:col-span-5">
            <div className="glass-card rounded-lg p-6 md:p-8 mb-6">
              <h3 className="text-xl font-semibold mb-4">Getting Started</h3>
              <ol className="space-y-4 list-decimal ml-5">
                <li>Create a TestNet wallet using the Wallet page</li>
                <li>Fund your wallet with TestNet ALGO from the faucet</li>
                <li>
                  Start using natural language commands in the main dashboard to send tokens
                  or mint NFTs
                </li>
                <li>View your transaction history in the Transactions page</li>
              </ol>
              <div className="mt-6">
                <Button className="w-full">Create Wallet</Button>
              </div>
            </div>

            <div className="glass-card rounded-lg p-6 md:p-8">
              <h3 className="text-xl font-semibold mb-4">Example Commands</h3>
              <div className="space-y-2">
                <div className="bg-muted p-3 rounded-md text-sm">
                  "Send 10 ALGO to address XYZ123"
                </div>
                <div className="bg-muted p-3 rounded-md text-sm">
                  "Mint an NFT named 'Digital Art' with description 'My first artwork'"
                </div>
                <div className="bg-muted p-3 rounded-md text-sm">
                  "Check my wallet balance"
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mb-12">
          <h2 className="text-2xl font-semibold mb-6">Frequently Asked Questions</h2>
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="item-1">
              <AccordionTrigger>Is this running on the Algorand MainNet?</AccordionTrigger>
              <AccordionContent>
                No, Algo-Intent currently operates exclusively on the Algorand TestNet. This allows
                users to experiment and learn without using real funds. We plan to add MainNet
                support in future updates.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="item-2">
              <AccordionTrigger>How secure is my wallet?</AccordionTrigger>
              <AccordionContent>
                Your wallet is secured with password encryption. We never store your private
                keys on our servers - all sensitive operations happen client-side in your
                browser. Additionally, we recommend enabling two-factor authentication for
                added security.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="item-3">
              <AccordionTrigger>What types of NFTs can I mint?</AccordionTrigger>
              <AccordionContent>
                You can mint standard Algorand Standard Assets (ASAs) with customizable name,
                description, and image. In future updates, we plan to support more complex
                NFT structures with additional metadata, royalty settings, and collection
                grouping.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="item-4">
              <AccordionTrigger>Can I use voice commands instead of typing?</AccordionTrigger>
              <AccordionContent>
                Voice command functionality is currently in development and will be available
                in a future update. Stay tuned!
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </div>
    </Layout>
  );
};

export default About;
