# Algo-Intent

**Algo Intent** is an AI-powered Telegram bot that lets you manage Algorand wallets, send ALGO, create and transfer NFTs, and interact with Algorand assets using natural language — all from your Telegram chat.

---

## 🚀 Features

- **AI Intent Parsing:** Just type what you want to do in plain English, the bot understands and executes it.
- **Secure Wallet Management:** Create, connect, and disconnect Algorand wallets with password protection.
- **Send ALGO:** Transfer ALGO to one or multiple recipients, with atomic group support.
- **NFT Support:** Create NFTs (with images or videos), transfer NFTs, opt-in/out of assets.
- **IPFS Integration:** NFT media is uploaded to IPFS via Pinata for decentralized storage.
- **Permission-Based Security:** Every transaction requires explicit password approval.
- **Automatic Message Deletion:** Sensitive info (passwords, mnemonics) is deleted from chat after use.
- **TestNet & MainNet Support:** Easily switch between Algorand networks.

---

## 📝 Example Telegram Commands

Copy-paste or type these directly to the bot:

```
create me a new wallet

I want to connect my wallet

send 2 algos to this address K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4

Create 10 nfts with name Universe and give it description "This image shows our milky way"

send 2 algos to both K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4 and 6MZK4765UUZFBPAPXZBNXTIRHORJ75KBKRIGHVOB23OQODVMSB6GCL5DVM

Opt in for NFT 740574628

Opt out of NFT 740574628

Send NFT 740830836 to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4

Disconnect my wallet
```

You can also send images or videos with captions like  
`Create NFT named "Sunset" with description "Evening view"`  
to mint NFTs with media!

---

## 📦 Installation

1. **Clone the repository:**
    ```
    git clone https://github.com/caerlower/algo-intent.git
    cd algo-intent
    ```

2. **Install dependencies:**
    ```
    pip install -r requirements.txt
    ```

3. **Configure environment variables:**
    - Fillout these fields in `.env` file
        - `TELEGRAM_BOT_TOKEN` (from @BotFather)
        - `ALGOD_ADDRESS`, `ALGOD_TOKEN` (Algorand node)
        - `PINATA_API_KEY`, `PINATA_API_SECRET` (for IPFS uploads)
        - `PERPLEXITY_API_KEY` (for AI intent parsing)

4. **Run the bot:**
    ```
    python telegram_bot.py
    ```

---

## 🗂️ Project Structure

```
algo-intent-bot/
├── telegram_bot.py        # Main Telegram bot logic
├── ai_intent.py           # AI-powered intent parser
├── wallet.py              # Wallet management and encryption
├── transaction_builder.py # Algorand transaction builder and sender
├── ipfs_utils.py          # IPFS integration for NFT media
├── utils.py               # Helper utilities
└── requirements.txt
```

## 🔒 Security

- **Sensitive data deletion:** Passwords and mnemonics are never stored or logged, and are erased from chat after use.
- **Session management:** Sessions auto-expire after inactivity.
- **Rate limiting:** Prevents spam and abuse.
- **Explicit approval:** Every transaction requires password confirmation.

---

## 🛡️ Troubleshooting & Tips

- **Transaction says failed but went through?**  
  Always check the provided TxID in [Pera Explorer](https://testnet.explorer.perawallet.app) or [AlgoExplorer](https://algoexplorer.io/) for final status.
- **NFT/ALGO not received?**  
  - Ensure the recipient has opted-in (for NFTs).
  - Check your wallet balance and transaction history.
  - Use `/check_tx <txid>` to check transaction status.
- **Bot doesn't understand my command?**  
  Try rephrasing or use the example commands above.
- **Lost wallet access?**  
  If you have your mnemonic (recovery phrase), you can always restore your wallet.  
  _The bot cannot recover lost mnemonics or passwords._

---

## 🌐 Supported Networks

| Network | Status  | Explorer Link                     |
|---------|---------|-----------------------------------|
| Testnet | ✅ Live | https://testnet.algoexplorer.io   |
| Mainnet | ✅ Live | https://algoexplorer.io           |

---

## 🤝 Contributing

Pull requests, issues, and feature suggestions are welcome!  
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙋 FAQ

- **Can I use this on mainnet?**  
  Yes, just set your `ALGOD_ADDRESS` to a mainnet node and fund your wallet with real ALGO.
- **Is my mnemonic/password safe?**  
  Yes. They are never stored or logged, and are erased from chat as soon as possible.
- **How does the bot understand my commands?**  
  It uses an AI-powered intent parser that extracts your intent and parameters from plain English.

---

## 🏁 Quick Demo

![Demo Screenshot](demo/demo1.png)

---

Thank you for using **Algo-Intent**!  
Happy building on Algorand 🚀

```
