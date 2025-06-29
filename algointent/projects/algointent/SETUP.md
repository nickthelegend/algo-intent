# Quick Setup Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies
```bash
npm install
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root:

```env
# Required: AI Intent Parsing
VITE_PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Optional: IPFS Upload (for NFT media)
VITE_PINATA_API_KEY=your_pinata_api_key_here
VITE_PINATA_API_SECRET=your_pinata_api_secret_here
```

### 3. Get API Keys

#### Perplexity API (Required)
1. Go to [perplexity.ai](https://perplexity.ai)
2. Sign up for a free account
3. Go to API settings
4. Copy your API key
5. Paste it in your `.env` file

#### Pinata API (Optional - for NFT media uploads)
1. Go to [pinata.cloud](https://pinata.cloud)
2. Sign up for a free account
3. Go to API Keys section
4. Create a new API key
5. Copy both the API Key and Secret
6. Paste them in your `.env` file

### 4. Start Development Server
```bash
npm run dev
```

### 5. Open Your Browser
Navigate to `http://localhost:5173`

### 6. Connect Your Wallet
1. Click "Connect Wallet" button
2. Choose your preferred wallet (Pera, Defly, or Exodus)
3. Make sure you're on TestNet for safe testing

### 7. Start Chatting!
Try these example commands:
- `send 1 ALGO to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4`
- `create NFT named "My First NFT"`
- `check my balance`

## 🔧 Troubleshooting

### Build Errors
If you get build errors, try:
```bash
npm run generate:app-clients
npm run build
```

### API Key Issues
- Make sure your API keys are correct
- Check that the `.env` file is in the project root
- Restart the dev server after adding API keys

### Wallet Connection Issues
- Make sure your wallet is on TestNet
- Try refreshing the page
- Check that your wallet extension is enabled

## 📱 Supported Wallets
- **Pera Wallet** (Recommended)
- **Defly Wallet**
- **Exodus Wallet**

## 🌐 Networks
- **TestNet** (Default - Safe for testing)
- **MainNet** (Change VITE_ALGOD_SERVER in .env)

## 🎯 Next Steps
1. Get some TestNet ALGO from the [Algorand TestNet Dispenser](https://bank.testnet.algorand.network/)
2. Try creating an NFT with an image
3. Send ALGO to friends
4. Explore the different commands

Happy building! 🚀 