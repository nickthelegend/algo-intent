import argparse
import sys
import json
import logging
from intent_parser import parse_intent, parse_nft_intent
from transaction_builder import build_and_send_transaction, TransactionError, create_nft, NFTCreationError
from utils import (
    get_algod_client,
    SENDER_ADDRESS,
    SENDER_MNEMONIC,
    generate_unit_name,
    normalize_number
)

def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('algo-intent')

def prompt_missing(field, prompt_text, default=None, is_number=False):
    value = input(f"📝 {prompt_text}" + (f" (default is {default}): " if default else ": "))
    value = value.strip()
    if not value and default is not None:
        return default
    if is_number:
        return normalize_number(value)
    return value

def main():
    parser = argparse.ArgumentParser(description="Algorand CLI AI Wallet")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # send-intent command
    send_parser = subparsers.add_parser('send-intent', help='Send ALGO using natural language')
    send_parser.add_argument('intent', help='Natural language instruction (e.g., "Send five algos to ADDRESS")')
    send_parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    send_parser.add_argument('--dry-run', action='store_true', help='Build transaction but do not send')

    # create-nft-intent command
    nft_parser = subparsers.add_parser('create-nft-intent', help='Create NFT from natural language intent')
    nft_parser.add_argument('intent', help='Natural language NFT creation instruction')
    nft_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # Handle send-intent
    if args.command == 'send-intent':
        logger = setup_logging(args.debug if hasattr(args, 'debug') else False)
        intent = parse_intent(args.intent)
        if not intent:
            print("❌ Could not parse your instruction. Please check your input.")
            print("Example: 'Send five algos to ADDRESS' or 'Transfer 10 algorand tokens to ADDRESS'")
            sys.exit(1)
        if args.debug:
            logger.debug(f"Parsed intent: {intent}")
        algod_client = get_algod_client()
        try:
            result = build_and_send_transaction(
                SENDER_ADDRESS,
                intent['recipient'],
                intent['amount'],
                algod_client,
                SENDER_MNEMONIC,
                dry_run=args.dry_run
            )
            print(result['message'])
            if args.debug and 'txid' in result:
                logger.debug(f"Transaction details: {result}")
        except TransactionError as e:
            print(str(e))
            sys.exit(1)

    # Handle create-nft-intent
    elif args.command == 'create-nft-intent':
        logger = setup_logging(args.debug if hasattr(args, 'debug') else False)
        parsed = parse_nft_intent(args.intent)
        if not parsed or not parsed.get("name"):
            print("❌ Could not parse NFT name from your instruction. Example: 'Create an NFT named BlueDragon'")
            return
        name = parsed.get("name")
        total_supply = parsed.get("total_supply") or prompt_missing(
            "total_supply", "Please enter total supply", default=1, is_number=True
        )
        description = parsed.get("description") or prompt_missing(
            "description", "Please enter description (optional)", default=""
        )
        unit_name = generate_unit_name(name)
        algod_client = get_algod_client()
        try:
            asset_id = create_nft(
                name=name,
                unit_name=unit_name,
                total_supply=total_supply,
                description=description,
                algod_client=algod_client,
                sender=SENDER_ADDRESS,
                sender_mnemonic=SENDER_MNEMONIC
            )
            result = {
                "asset_name": name,
                "unit_name": unit_name,
                "total_supply": total_supply,
                "creator": SENDER_ADDRESS,
                "status": "✅ NFT Created Successfully",
                "asset_id": asset_id
            }
            print(json.dumps(result, indent=2))
        except NFTCreationError as e:
            print(str(e))

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
