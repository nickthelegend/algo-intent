# Algo-Intent Web App

**Algo-Intent** is an AI-powered web application that lets you manage Algorand wallets, execute trades, and learn about blockchain technology using natural language — all through an intelligent chat interface.

## 🚀 Features

- **Advanced AI Intent Parsing:** Just type what you want to do in plain English, the AI understands complex requests and provides context-aware responses.
- **Secure Wallet Management:** Connect your Algorand wallet (Pera, Defly, Exodus) with one click.
- **Send ALGO:** Transfer ALGO to one or multiple recipients with atomic group support.
- **NFT Support:** Create NFTs (with images or videos), transfer NFTs, opt-in/out of assets.
- **Trading Operations:** Swap tokens, set limit orders, stop-loss orders, and check market prices.
- **Educational AI:** Ask questions about Algorand, DeFi, trading, and blockchain concepts.
- **IPFS Integration:** NFT media is uploaded to IPFS via Pinata for decentralized storage.
- **Beautiful UI:** Modern, responsive chat interface with real-time transaction status.
- **TestNet & MainNet Support:** Easily switch between Algorand networks.

## 📝 Example Commands

Type these directly in the chat interface:

### 💼 Wallet Operations
```
send 2 algos to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4

Create 10 nfts with name Universe and give it description "This image shows our milky way"

send 2 algos to both K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4 and 6MZK4765UUZFBPAPXZBNXTIRHORJ75KBKRIGHVOB23OQODVMSB6GCL5DVM

Opt in for NFT 740574628

Opt out of NFT 740574628

Send NFT 740830836 to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4

Check my balance
```

### 📈 Trading Operations
```
Swap 50 USDC to ALGO

Trade 100 ALGO when price reaches $0.22

Set stop-loss for 50 ALGO at $0.18

What's the current ALGO price?

Check market prices for Bitcoin and Ethereum
```

### 🎓 Educational Queries
```
What is Algorand?

How do NFTs work on Algorand?

Can I stake my ALGO?

Explain DeFi trading

What's the difference between proof-of-stake and proof-of-work?
```

You can also attach images or videos with captions like  
`Create NFT named "Sunset" with description "Evening view"`  
to mint NFTs with media!

## 🛠️ Installation

1. **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd algointent/projects/algointent
    ```

2. **Install dependencies:**
    ```bash
    npm install
    ```

3. **Configure environment variables:**
    Create a `.env` file in the project root with the following variables:
    ```env
    # Algorand Network Configuration
    VITE_ALGOD_SERVER=https://testnet-api.algonode.cloud
    VITE_ALGOD_PORT=443
    VITE_ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

    # AI Intent Parsing (Perplexity API)
    VITE_PERPLEXITY_API_KEY=your_perplexity_api_key_here

    # Market Data (CoinGecko API - Optional)
    VITE_COINGECKO_API_KEY=your_coingecko_api_key_here

    # IPFS Upload (Pinata API)
    VITE_PINATA_API_KEY=your_pinata_api_key_here
    VITE_PINATA_API_SECRET=your_pinata_api_secret_here
    ```

4. **Get API Keys:**
    - **Perplexity API:** Sign up at [perplexity.ai](https://perplexity.ai) to get your API key
    - **CoinGecko API:** Sign up at [coingecko.com](https://coingecko.com) for market data (optional)
    - **Pinata API:** Sign up at [pinata.cloud](https://pinata.cloud) to get your API keys

5. **Run the development server:**
    ```bash
    npm run dev
    ```

6. **Open your browser:**
    Navigate to `http://localhost:5173`

## 🗂️ Project Structure

```
src/
├── components/
│   ├── AlgoIntentChat.tsx    # Main chat interface
│   ├── ConnectWallet.tsx     # Wallet connection modal
│   ├── Transact.tsx          # Transaction demo modal
│   └── ...
├── services/
│   ├── aiIntentService.ts    # AI intent parsing
│   ├── transactionService.ts # Algorand transactions
│   ├── tradingService.ts     # Trading operations
│   └── ipfsService.ts        # IPFS integration
├── utils/
│   └── network/              # Network configuration
└── ...
```

## 🔒 Security

- **Client-side only:** All operations happen in your browser, no server-side storage of sensitive data.
- **Wallet integration:** Uses official Algorand wallet connectors (Pera, Defly, Exodus).
- **Secure transactions:** All transactions require explicit wallet approval.
- **Environment variables:** API keys are stored locally and never exposed.

## 🌐 Supported Networks

| Network | Status  | Explorer Link                          |
|---------|---------|----------------------------------------|
| Testnet | ✅ Live | https://testnet.explorer.perawallet.app|
| Mainnet | ⚠️ Beta | https://explorer.perawallet.app/       |

## 🛡️ Troubleshooting & Tips

- **Transaction says failed but went through?**  
  Always check the provided TxID in [Pera Explorer](https://testnet.explorer.perawallet.app) for final status.
- **NFT/ALGO not received?**  
  - Ensure the recipient has opted-in (for NFTs).
  - Check your wallet balance and transaction history.
- **App doesn't understand my command?**  
  Try rephrasing or use the example commands above.
- **File upload failed?**  
  - Check your Pinata API keys are correct.
  - Ensure file size is under 1GB.
  - Try uploading a smaller file first.
- **Trading features not working?**  
  - Trading operations are currently simulated for demonstration.
  - Real DEX integration requires additional smart contract deployment.

## 🤝 Contributing

Pull requests, issues, and feature suggestions are welcome!  

## 📜 License

MIT License - See [LICENSE](LICENSE) for details

## 🙋 FAQ

- **Can I use this on mainnet?**  
  Yes, just change your `VITE_ALGOD_SERVER` to a mainnet node and fund your wallet with real ALGO.
- **Is my wallet safe?**  
  Yes. The app only requests permission to sign transactions, never has access to your private keys.
- **How does the app understand my commands?**  
  It uses an advanced AI-powered intent parser that extracts your intent and parameters from plain English, with deep knowledge of Algorand and blockchain concepts.
- **What wallets are supported?**  
  Pera Wallet, Defly Wallet, and Exodus Wallet are currently supported.
- **Are the trading features real?**  
  Currently, trading operations are simulated for demonstration. Real DEX integration would require smart contract deployment and additional development.

---

Thank you for using **Algo-Intent**!  
Happy building on Algorand 🚀

Build For Hack Series 2025
