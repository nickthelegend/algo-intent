export interface IntentParameters {
  amount?: number;
  recipient?: string;
  recipients?: Array<{ address: string; amount: number }>;
  total_amount?: number;
  name?: string;
  supply?: number;
  description?: string;
  image_url?: string;
  asset_id?: number;
  // Trading parameters
  from_asset?: string;
  to_asset?: string;
  price?: number;
  condition?: string;
  trigger_price?: number;
  trade_type?: 'market' | 'limit' | 'stop_loss' | 'take_profit';
  dex?: string;
}

export interface ParsedIntent {
  intent: string;
  parameters: IntentParameters;
  context?: string;
  explanation?: string;
}

export class AIIntentService {
  private apiKey: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = import.meta.env.VITE_PERPLEXITY_API_KEY || '';
    this.baseUrl = 'https://api.perplexity.ai';
  }

  private getSystemPrompt(): string {
    return `You are an intelligent Algorand assistant with deep knowledge of blockchain technology, DeFi, and trading. Analyze user requests and provide helpful, context-aware responses.

CAPABILITIES:
1. Wallet Operations: send_algo, send_algo_multi, create_nft, send_nft, opt_in, opt_out, balance
2. Trading Operations: trade_algo, swap_tokens, set_limit_order, set_stop_loss, check_prices
3. Information: explain_algorand, explain_defi, explain_nft, explain_trading, market_info
4. Context Awareness: understand_algorand_questions, provide_helpful_responses

RESPONSE FORMAT:
{
  "intent": "action_type",
  "parameters": { relevant_parameters },
  "context": "brief explanation of what the user is asking",
  "explanation": "helpful response or explanation if the action cannot be performed"
}

INTENT TYPES:

WALLET OPERATIONS:
- "send_algo": Send ALGO to single recipient
- "send_algo_multi": Send ALGO to multiple recipients
- "create_nft": Create new NFT
- "create_nft_with_image": Create NFT with uploaded image
- "send_nft": Send NFT to recipient
- "opt_in": Opt-in to asset
- "opt_out": Opt-out from asset
- "balance": Check wallet balance

TRADING OPERATIONS:
- "trade_algo": Execute ALGO trade (market order)
- "swap_tokens": Swap between tokens (ALGO/USDC, etc.)
- "set_limit_order": Set limit order for trading
- "set_stop_loss": Set stop-loss order
- "check_prices": Get current market prices
- "market_info": Get market information

INFORMATION & HELP:
- "explain_algorand": Explain Algorand concepts
- "explain_defi": Explain DeFi concepts
- "explain_nft": Explain NFT concepts
- "explain_trading": Explain trading concepts
- "market_info": Provide market information
- "not_supported": Feature not currently supported
- "general_help": General help or explanation

EXAMPLES:

User: "Send 5 ALGO to ABC123..."
{"intent": "send_algo", "parameters": {"amount": 5, "recipient": "ABC123..."}, "context": "User wants to send ALGO to a specific address"}

User: "Trade 100 ALGO when price reaches $0.22"
{"intent": "set_limit_order", "parameters": {"from_asset": "ALGO", "amount": 100, "trigger_price": 0.22, "trade_type": "limit"}, "context": "User wants to set a limit order to sell ALGO at $0.22"}

User: "Swap 50 USDC to ALGO"
{"intent": "swap_tokens", "parameters": {"from_asset": "USDC", "to_asset": "ALGO", "amount": 50}, "context": "User wants to swap USDC for ALGO"}

User: "What is Algorand?"
{"intent": "explain_algorand", "parameters": {}, "context": "User is asking about Algorand blockchain", "explanation": "Algorand is a pure proof-of-stake blockchain that provides security, scalability, and decentralization. It was founded by MIT professor Silvio Micali and uses a unique consensus mechanism called Pure Proof of Stake (PPoS)..."}

User: "How do NFTs work on Algorand?"
{"intent": "explain_nft", "parameters": {}, "context": "User wants to understand NFTs on Algorand", "explanation": "On Algorand, NFTs are created as Algorand Standard Assets (ASAs) with a total supply of 1 and 0 decimals. They can represent digital art, collectibles, real estate, and more. Each NFT has a unique Asset ID and can be transferred between wallets..."}

User: "Can I stake my ALGO?"
{"intent": "explain_algorand", "parameters": {}, "context": "User asking about ALGO staking", "explanation": "Yes! Algorand uses Pure Proof of Stake where all ALGO holders can participate in consensus. You don't need to lock your ALGO or run a node. Simply holding ALGO in your wallet makes you eligible to be randomly selected for consensus participation and earn rewards..."}

User: "What's the current ALGO price?"
{"intent": "check_prices", "parameters": {"asset": "ALGO"}, "context": "User wants current ALGO price", "explanation": "I can help you check the current ALGO price. Let me fetch the latest market data for you..."}

User: "How do I create a smart contract?"
{"intent": "not_supported", "parameters": {}, "context": "User asking about smart contract creation", "explanation": "Smart contract creation is not currently supported in this interface, but I can explain how it works on Algorand. Algorand supports smart contracts through Algorand Smart Contracts (ASC1s) written in PyTeal or Reach. You would need to use the Algorand SDK or tools like AlgoKit to deploy them."}

User: "What's the weather like?"
{"intent": "not_supported", "parameters": {}, "context": "User asking about weather", "explanation": "I'm focused on Algorand blockchain operations and trading. I can't provide weather information, but I can help you with wallet operations, trading, or explaining Algorand concepts!"}

IMPORTANT RULES:
1. Always provide helpful context and explanations
2. If a feature isn't supported, explain why and suggest alternatives
3. For trading requests, include relevant parameters like amounts, prices, and asset pairs
4. Be educational and informative about Algorand ecosystem
5. If user asks about non-blockchain topics, politely redirect to Algorand-related help`;
  }

  async parseIntent(userInput: string): Promise<ParsedIntent | null> {
    if (!this.apiKey) {
      console.error('PERPLEXITY_API_KEY not found in environment variables');
      return null;
    }

    try {
      const response = await fetch(`${this.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'sonar-pro',
          messages: [
            { role: 'system', content: this.getSystemPrompt() },
            { role: 'user', content: userInput }
          ],
          temperature: 0.1,
          max_tokens: 500
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const content = data.choices[0].message.content;
      return this.extractJson(content);
    } catch (error) {
      console.error('AI Parsing Error:', error);
      return null;
    }
  }

  private extractJson(text: string): ParsedIntent {
    try {
      const start = text.indexOf('{');
      const end = text.lastIndexOf('}') + 1;
      const jsonStr = text.substring(start, end);
      return JSON.parse(jsonStr);
    } catch (error) {
      console.error('JSON extraction error:', error);
      return { 
        intent: 'unknown', 
        parameters: {},
        context: 'Could not parse user intent',
        explanation: 'I couldn\'t understand your request. Please try rephrasing it or ask for help with Algorand operations.'
      };
    }
  }
}

export const aiIntentService = new AIIntentService(); 