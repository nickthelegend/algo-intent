
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Mic, Send } from "lucide-react";

interface CommandInputProps {
  onSubmit: (command: string) => void;
  isProcessing?: boolean;
}

const CommandInput: React.FC<CommandInputProps> = ({ onSubmit, isProcessing = false }) => {
  const [command, setCommand] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (command.trim() && !isProcessing) {
      onSubmit(command.trim());
      setCommand("");
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative w-full">
        <div className="relative flex items-center">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Type your command (e.g. 'Send 10 ALGO to address XYZ')"
            className="w-full rounded-lg border bg-background px-4 py-2.5 pr-20 text-sm shadow-sm focus:ring-2 focus:ring-primary focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isProcessing}
          />
          <div className="absolute right-1.5 flex items-center gap-1.5">
            <Button
              type="button"
              size="icon"
              variant="ghost"
              className="h-7 w-7 rounded-full"
              disabled={isProcessing}
              title="Voice command (coming soon)"
            >
              <Mic className="size-4" />
              <span className="sr-only">Voice command</span>
            </Button>
            <Button
              type="submit"
              size="icon"
              variant="secondary"
              className="h-7 w-7 rounded-full"
              disabled={!command.trim() || isProcessing}
            >
              <Send className="size-4" />
              <span className="sr-only">Submit</span>
            </Button>
          </div>
        </div>
        <div className="mt-1.5 flex justify-between px-1 text-xs text-muted-foreground">
          <p>Enter a natural language command to execute on Algorand TestNet</p>
          {command.length > 0 && (
            <p>{command.length} character{command.length !== 1 ? 's' : ''}</p>
          )}
        </div>
      </form>
    </div>
  );
};

export default CommandInput;
