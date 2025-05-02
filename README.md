# Algo-Intent

An ai agent that understands natural language instructions for sending ALGO and creating NFTs on the Algorand TestNet, there are not many features for now it's still under developement. I have hard code most of the stuff right now, will be adding AI for intent parsing as the development move forward.

## Features (For now)

- **Natural Language Processing**: Send transactions using plain English commands
- **Secure Wallet Management**: Create and connect wallets with password protection
- **NFT Creation**: Mint NFTs with customizable properties using natural language
- **Permission-Based Security**: Explicit transaction approval with password verification
- **TestNet Support**: Built for Algorand TestNet development and testing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/alog-intent.git
cd algo-intent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Wallet Management

**Create a new wallet:**
```bash
python app.py create-wallet
```

**Connect an existing wallet:**
```bash
python app.py connect-wallet
```

**List saved wallets:**
```bash
python app.py list-wallets
```

**Disconnect current wallet:**
```bash
python app.py disconnect-wallet
```

### Sending ALGO

Send ALGO using natural language instructions:

NOTE: I have given a default address in this readme so you don't have to worry about finding an address.

```bash
python app.py send-intent "Send five algos to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4"
```

The wallet supports various ways to express the same intent:
```bash
python app.py send-intent "Transfer 10 algorand tokens to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4"
python app.py send-intent "Send 0.5 native algo to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4"
python app.py send-intent "Send 1 algorand cryptocurrency to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4"
```

You can also use text numbers:
```bash
python app.py send-intent "Send five point five algos to K54ZTTHNDB567Q5J5T73CEJCT3Z3MB6VL35PJBIX57KGRWNGZZLH3BK7S4"
```

### Creating NFTs

Create NFTs using natural language:

```bash
python app.py create-nft-intent "Create an NFT named BlueDragon"
```

You can specify additional properties:
```bash
python app.py create-nft-intent "Create an NFT called MoonCat with description Cute space cat collection"
python app.py create-nft-intent "Mint NFT named PixelArt with supply five"
```

## Security

- Private keys and mnemonics are encrypted with a password
- Each transaction requires explicit approval and password verification
- The application never directly handles unencrypted private keys
- Wallet data is stored in separate encrypted files

## Project Structure

- `app.py`: Main CLI interface with subcommands
- `wallet.py`: Wallet management (creation, connection, signing)
- `intent_parser.py`: Natural language parsing for transactions and NFTs
- `transaction_builder.py`: Builds and submits Algorand transactions
- `utils.py`: Utility functions for token handling, text processing, etc.

## Requirements

- Python 3.10+
- py-algorand-sdk
- python-dotenv
- cryptography

## Future Development - currently working on this

- Integration with AI for advanced intent parsing
- Support for ASA tokens beyond native ALGO (no support on testnet)
- Web interfaces
- MainNet support with enhanced security
