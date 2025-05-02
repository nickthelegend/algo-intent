import argparse
import sys
import json
import logging
from intent_parser import parse_intent, parse_nft_intent
from transaction_builder import build_and_send_transaction, TransactionError, create_nft, NFTCreationError
from utils import get_algod_client, generate_unit_name
from wallet import (
    create_wallet, 
    connect_wallet, 
    disconnect_wallet,
    get_connected_wallet, 
    list_wallets,
    format_wallet_display
)

def setup_logging(debug=False):
    """Configure logging based on debug flag"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('algo-intent')

def prompt_missing(field, prompt_text, default=None, is_number=False):
    """Prompt user for missing information with optional default value"""
    value = input(f"📝 {prompt_text}" + (f" (default is {default}): " if default else ": "))
    value = value.strip()
    if not value and default is not None:
        return default
    if is_number:
        try:
            return int(value)
        except ValueError:
            return default
    return value

def ensure_wallet_connected():
    """Check if a wallet is connected and prompt to connect one if not"""
    wallet = get_connected_wallet()
    if not wallet:
        print("❌ No wallet connected.")
        action = input("Would you like to (1) create a new wallet or (2) connect an existing one? (1/2): ")
        
        if action == "1":
            try:
                wallet_data = create_wallet()
                print("\n✅ New wallet created!")
                print(f"Address: {wallet_data['address']}")
                print(f"Mnemonic: {wallet_data['mnemonic']}")
                print(f"\n{wallet_data['message']}")
                return True
            except Exception as e:
                print(f"❌ Error creating wallet: {e}")
                return False
        elif action == "2":
            try:
                wallet_data = connect_wallet()
                print("\n✅ Wallet connected successfully!")
                print(f"Address: {wallet_data['address']}")
                return True
            except Exception as e:
                print(f"❌ Error connecting wallet: {e}")
                return False
        else:
            print("Please connect a wallet before performing transactions.")
            return False
    return True

def main():
    """Main CLI entry point with subcommands for wallet management and transactions"""
    parser = argparse.ArgumentParser(description="Algorand AI Wallet Assistant")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Wallet management commands
    create_wallet_parser = subparsers.add_parser('create-wallet', help='Create a new Algorand wallet')
    
    connect_wallet_parser = subparsers.add_parser('connect-wallet', help='Connect an existing Algorand wallet')
    
    disconnect_wallet_parser = subparsers.add_parser('disconnect-wallet', help='Disconnect the current wallet')
    
    list_wallets_parser = subparsers.add_parser('list-wallets', help='List all saved wallets')
    
    # Intent commands
    send_parser = subparsers.add_parser('send-intent', help='Send ALGO using natural language')
    send_parser.add_argument('intent', help='Natural language instruction (e.g., "Send five algos to ADDRESS")')
    send_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    send_parser.add_argument('--dry-run', action='store_true', help='Build transaction but do not send')

    # NFT commands
    nft_parser = subparsers.add_parser('create-nft-intent', help='Create NFT from natural language intent')
    nft_parser.add_argument('intent', help='Natural language NFT creation instruction')
    nft_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()
    
    # No command provided
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Wallet creation
    if args.command == 'create-wallet':
        try:
            wallet_data = create_wallet()
            print("\n✅ New wallet created!")
            print(f"Address: {wallet_data['address']}")
            print(f"Mnemonic: {wallet_data['mnemonic']}")
            print(f"\n{wallet_data['message']}")
        except Exception as e:
            print(f"❌ Error creating wallet: {e}")
            sys.exit(1)

    # Wallet connection
    elif args.command == 'connect-wallet':
        try:
            wallet_data = connect_wallet()
            print("\n✅ Wallet connected successfully!")
            print(f"Address: {wallet_data['address']}")
        except Exception as e:
            print(f"❌ Error connecting wallet: {e}")
            sys.exit(1)
    
    # Wallet disconnection
    elif args.command == 'disconnect-wallet':
        try:
            result = disconnect_wallet()
            print(f"✅ {result['message']}")
        except Exception as e:
            print(f"❌ Error disconnecting wallet: {e}")
            sys.exit(1)
    
    # List wallets
    elif args.command == 'list-wallets':
        try:
            wallets = list_wallets()
            if not wallets:
                print("No wallets found.")
            else:
                print("\nSaved Wallets:")
                for wallet in wallets:
                    status = "🟢 Active" if wallet["active"] else "⚪️ Inactive"
                    print(f"{status} - {wallet['address']}")
        except Exception as e:
            print(f"❌ Error listing wallets: {e}")
            sys.exit(1)

    # Send intent
    elif args.command == 'send-intent':
        logger = setup_logging(args.debug if hasattr(args, 'debug') else False)
        
        # Ensure wallet is connected before proceeding
        if not ensure_wallet_connected():
            sys.exit(1)
            
        intent = parse_intent(args.intent)
        if not intent:
            print("❌ Could not parse your instruction. Please check your input.")
            print("Example: 'Send five algos to ADDRESS' or 'Transfer 10 algorand tokens to ADDRESS'")
            sys.exit(1)
            
        if args.debug:
            logger.debug(f"Parsed intent: {intent}")
            
        try:
            # Get the connected wallet
            wallet = get_connected_wallet()
            algod_client = get_algod_client()
            
            result = build_and_send_transaction(
                wallet["address"],  # Use wallet address as sender
                intent['recipient'],
                intent['amount'],
                algod_client,
                dry_run=args.dry_run
            )
            print(result['message'])
            if args.debug and 'txid' in result:
                logger.debug(f"Transaction details: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    # Create NFT intent
    elif args.command == 'create-nft-intent':
        logger = setup_logging(args.debug if hasattr(args, 'debug') else False)
        
        # Ensure wallet is connected before proceeding
        if not ensure_wallet_connected():
            sys.exit(1)
            
        # Get the connected wallet
        try:
            wallet = get_connected_wallet()
            
            parsed = parse_nft_intent(args.intent)
            if not parsed or not parsed.get("name"):
                print("❌ Could not parse NFT name from your instruction. Example: 'Create an NFT named BlueDragon'")
                return

            # Prompt for missing fields
            name = parsed.get("name")
            total_supply = parsed.get("total_supply") or prompt_missing(
                "total_supply", "Please enter total supply", default=1, is_number=True
            )
            description = parsed.get("description") or prompt_missing(
                "description", "Please enter description (optional)", default=""
            )
            unit_name = generate_unit_name(name)

            algod_client = get_algod_client()
            asset_id = create_nft(
                name=name,
                unit_name=unit_name,
                total_supply=total_supply,
                description=description,
                algod_client=algod_client,
                sender=wallet["address"]
            )
            result = {
                "asset_name": name,
                "unit_name": unit_name,
                "total_supply": total_supply,
                "creator": wallet["address"],
                "status": "✅ NFT Created Successfully",
                "asset_id": asset_id
            }
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
