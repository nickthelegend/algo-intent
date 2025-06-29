import { algo, AlgorandClient } from '@algorandfoundation/algokit-utils';
import algosdk from 'algosdk';

export interface TransactionResult {
  status: 'success' | 'error' | 'pending';
  txid?: string;
  message: string;
  error?: string;
}

export interface NFTMetadata {
  name: string;
  unitName: string;
  totalSupply: number;
  description?: string;
  url?: string;
}

const ALGOD_SERVER = 'https://testnet-api.algonode.cloud';
const ALGOD_TOKEN = '';
const ALGOD_PORT = '';

export async function getAccountBalance(address: string): Promise<{ algo: number; assets: any[] }> {
  if (!algosdk.isValidAddress(address)) throw new Error('Invalid Algorand address');
  const algod = new algosdk.Algodv2(ALGOD_TOKEN, ALGOD_SERVER, ALGOD_PORT);
  const info = await algod.accountInformation(address).do();
  return {
    algo: Number(info.amount) / 1_000_000,
    assets: info.assets || []
  };
}

export async function sendAlgo(sender: string, recipient: string, amount: number, signer: any) {
  if (!algosdk.isValidAddress(sender) || !algosdk.isValidAddress(recipient)) throw new Error('Invalid address');
  const algod = new algosdk.Algodv2(ALGOD_TOKEN, ALGOD_SERVER, ALGOD_PORT);
  const params = await algod.getTransactionParams().do();
  const txn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
    from: sender,
    to: recipient,
    amount: Math.floor(amount * 1_000_000),
    suggestedParams: params
  } as any);
  const signedTxn = await signer([txn]);
  const txid = await algod.sendRawTransaction(signedTxn[0].blob).do();
  await algosdk.waitForConfirmation(algod, txid.txid, 4);
  return txid.txid;
}

export async function sendAlgoMulti(
  sender: string,
  recipients: Array<{ address: string; amount: number }>,
  signer: any
): Promise<TransactionResult> {
  try {
    if (recipients.length < 2) {
      return {
        status: 'error',
        message: '❌ Multi-recipient transfer requires at least 2 recipients.',
        error: 'Invalid recipients'
      };
    }

    // Validate all recipients
    for (let i = 0; i < recipients.length; i++) {
      const recipient = recipients[i];
      if (!algosdk.isValidAddress(recipient.address)) {
        return {
          status: 'error',
          message: `❌ Invalid recipient address #${i + 1}`,
          error: 'Invalid address'
        };
      }
      if (recipient.amount <= 0) {
        return {
          status: 'error',
          message: `❌ Invalid amount for recipient #${i + 1}`,
          error: 'Invalid amount'
        };
      }
    }

    // Use algokit-utils AtomicTransactionComposer for proper group handling
    const atc = new algosdk.AtomicTransactionComposer();
    
    // Get algod client from stored configuration
    const algod = new algosdk.Algodv2(
      ALGOD_TOKEN,
      ALGOD_SERVER,
      ALGOD_PORT
    );
    
    // Add each payment transaction to the composer
    for (const recipient of recipients) {
      const paymentTxn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
        from: sender,
        to: recipient.address,
        amount: Math.floor(recipient.amount * 1_000_000),
        suggestedParams: await algod.getTransactionParams().do(),
        note: new TextEncoder().encode(`Multi-recipient transfer to ${recipient.address}`)
      } as any);
      
      atc.addTransaction({
        txn: paymentTxn,
        signer: signer
      });
    }

    // Execute the atomic group
    const result = await atc.execute(algod, 5);

    return {
      status: 'success',
      txid: result.txIDs[0], // First transaction ID represents the group
      message: `✅ Atomic multi-recipient transfer successful! ${recipients.length} payments sent atomically. Group TxID: ${result.txIDs[0]}`
    };

  } catch (error) {
    return {
      status: 'error',
      message: `❌ Atomic multi-recipient transfer failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

export async function createNFT(sender: string, metadata: { name: string; unitName: string; totalSupply: number; description?: string; url?: string }, signer: any) {
  if (!algosdk.isValidAddress(sender)) throw new Error('Invalid sender address');
  const algod = new algosdk.Algodv2(ALGOD_TOKEN, ALGOD_SERVER, ALGOD_PORT);
  const params = await algod.getTransactionParams().do();
  const txn = algosdk.makeAssetCreateTxnWithSuggestedParamsFromObject({
    from: sender,
    total: BigInt(metadata.totalSupply),
    decimals: 0,
    assetName: metadata.name.substring(0, 32),
    unitName: metadata.unitName.substring(0, 8),
    manager: sender,
    reserve: sender,
    freeze: sender,
    clawback: sender,
    url: metadata.url || '',
    note: metadata.description ? new TextEncoder().encode(metadata.description) : undefined,
    suggestedParams: params
  } as any);
  const signedTxn = await signer([txn]);
  const txid = await algod.sendRawTransaction(signedTxn[0].blob).do();
  const confirmed = await algosdk.waitForConfirmation(algod, txid.txid, 4);
  const assetId = confirmed['assetIndex'];
  if (typeof assetId !== 'number') throw new Error('Failed to get assetId after NFT creation');
  // Auto-opt-in after creation
  await optInToAsset(sender, assetId, signer);
  return { txid: txid.txid, assetId };
}

export async function optInToAsset(address: string, assetId: number, signer: any) {
  if (!algosdk.isValidAddress(address)) throw new Error('Invalid address');
  const algod = new algosdk.Algodv2(ALGOD_TOKEN, ALGOD_SERVER, ALGOD_PORT);
  const params = await algod.getTransactionParams().do();
  const txn = algosdk.makeAssetTransferTxnWithSuggestedParamsFromObject({
    from: address,
    to: address,
    assetIndex: assetId,
    amount: 0,
    suggestedParams: params
  } as any);
  const signedTxn = await signer([txn]);
  const txid = await algod.sendRawTransaction(signedTxn[0].blob).do();
  await algosdk.waitForConfirmation(algod, txid.txid, 4);
  return txid.txid;
}

export class TransactionService {
  private algorand: AlgorandClient;
  private algodConfig: any;

  constructor(algodConfig: any) {
    this.algorand = AlgorandClient.fromConfig({ algodConfig });
    this.algodConfig = algodConfig;
  }

  async getAccountBalance(address: string): Promise<{ algo: number; assets: any[] }> {
    try {
      if (!this.isValidAddress(address)) {
        throw new Error('Invalid Algorand address');
      }

      // Use algosdk directly with stored configuration
      const algod = new algosdk.Algodv2(
        this.algodConfig.token || '',
        this.algodConfig.server,
        this.algodConfig.port || ''
      );

      const accountInfo = await algod.accountInformation(address).do();

      return {
        algo: Number(accountInfo.amount) / 1_000_000, // Convert from microAlgos to ALGO
        assets: accountInfo.assets || []
      };
    } catch (error) {
      console.error('Error fetching account balance:', error);
      throw new Error(`Failed to fetch account balance: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Removed getAccountInformation method due to API compatibility issues

  async sendAlgo(
    sender: string,
    recipient: string,
    amount: number,
    signer: any
  ): Promise<TransactionResult> {
    try {
      // Validate address
      if (!this.isValidAddress(recipient)) {
        return {
          status: 'error',
          message: '❌ Invalid recipient address format.',
          error: 'Invalid address'
        };
      }

      // Send transaction using algokit-utils
      const result = await this.algorand.send.payment({
        signer: signer,
        sender: sender,
        receiver: recipient,
        amount: algo(amount),
      });

      return {
        status: 'success',
        txid: result.txIds[0],
        message: `✅ Transaction successful! ${amount.toFixed(6)} ALGO sent to ${recipient}. TxID: ${result.txIds[0]}`
      };

    } catch (error) {
      return {
        status: 'error',
        message: `❌ Transaction failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async sendAlgoMulti(
    sender: string,
    recipients: Array<{ address: string; amount: number }>,
    signer: any
  ): Promise<TransactionResult> {
    try {
      if (recipients.length < 2) {
        return {
          status: 'error',
          message: '❌ Multi-recipient transfer requires at least 2 recipients.',
          error: 'Invalid recipients'
        };
      }

      // Validate all recipients
      for (let i = 0; i < recipients.length; i++) {
        const recipient = recipients[i];
        if (!this.isValidAddress(recipient.address)) {
          return {
            status: 'error',
            message: `❌ Invalid recipient address #${i + 1}`,
            error: 'Invalid address'
          };
        }
        if (recipient.amount <= 0) {
          return {
            status: 'error',
            message: `❌ Invalid amount for recipient #${i + 1}`,
            error: 'Invalid amount'
          };
        }
      }

      // Use algokit-utils AtomicTransactionComposer for proper group handling
      const atc = new algosdk.AtomicTransactionComposer();
      
      // Get algod client from stored configuration
      const algod = new algosdk.Algodv2(
        this.algodConfig.token || '',
        this.algodConfig.server,
        this.algodConfig.port || ''
      );
      
      // Add each payment transaction to the composer
      for (const recipient of recipients) {
        const paymentTxn = algosdk.makePaymentTxnWithSuggestedParamsFromObject({
          from: sender,
          to: recipient.address,
          amount: Math.floor(recipient.amount * 1_000_000),
          suggestedParams: await algod.getTransactionParams().do(),
          note: new TextEncoder().encode(`Multi-recipient transfer to ${recipient.address}`)
        } as any);
        
        atc.addTransaction({
          txn: paymentTxn,
          signer: signer
        });
      }

      // Execute the atomic group
      const result = await atc.execute(algod, 5);

      return {
        status: 'success',
        txid: result.txIDs[0], // First transaction ID represents the group
        message: `✅ Atomic multi-recipient transfer successful! ${recipients.length} payments sent atomically. Group TxID: ${result.txIDs[0]}`
      };

    } catch (error) {
      return {
        status: 'error',
        message: `❌ Atomic multi-recipient transfer failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async createNFT(
    sender: string,
    metadata: NFTMetadata,
    signer: any
  ): Promise<TransactionResult> {
    try {
      if (!metadata.name) {
        return {
          status: 'error',
          message: '❌ NFT name is required.',
          error: 'Missing name'
        };
      }

      // Create NFT using algokit-utils
      const result = await this.algorand.send.assetCreate({
        signer: signer,
        sender: sender,
        assetName: metadata.name.substring(0, 32),
        unitName: metadata.unitName.substring(0, 8),
        total: BigInt(metadata.totalSupply),
        decimals: 0,
        manager: sender,
        reserve: sender,
        freeze: sender,
        clawback: sender,
        url: metadata.url || '',
        note: metadata.description ? new TextEncoder().encode(metadata.description) : undefined,
      });

      return {
        status: 'success',
        txid: result.txIds[0],
        message: `✅ NFT created successfully! Asset ID: ${result.assetId}, Name: ${metadata.name}`
      };

    } catch (error) {
      return {
        status: 'error',
        message: `❌ NFT creation failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async sendNFT(
    sender: string,
    assetId: number,
    recipient: string,
    signer: any
  ): Promise<TransactionResult> {
    try {
      if (!this.isValidAddress(recipient)) {
        return {
          status: 'error',
          message: '❌ Invalid recipient address format.',
          error: 'Invalid address'
        };
      }

      // Transfer NFT using algokit-utils
      const result = await this.algorand.send.assetTransfer({
        signer: signer,
        sender: sender,
        receiver: recipient,
        assetId: BigInt(assetId),
        amount: 1n,
      });

      return {
        status: 'success',
        txid: result.txIds[0],
        message: `✅ NFT transferred successfully! Asset ID: ${assetId} sent to ${recipient}`
      };

    } catch (error) {
      return {
        status: 'error',
        message: `❌ NFT transfer failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async optInToAsset(
    sender: string,
    assetId: number,
    signer: any
  ): Promise<TransactionResult> {
    try {
      // Opt-in using algokit-utils
      const result = await this.algorand.send.assetOptIn({
        signer: signer,
        sender: sender,
        assetId: BigInt(assetId),
      });

      return {
        status: 'success',
        txid: result.txIds[0],
        message: `✅ Successfully opted in to asset ${assetId}`
      };

    } catch (error) {
      return {
        status: 'error',
        message: `❌ Opt-in failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async optOutOfAsset(
    sender: string,
    assetId: number,
    signer: any
  ): Promise<TransactionResult> {
    try {
      // Opt-out using algokit-utils
      const result = await this.algorand.send.assetOptOut({
        signer: signer,
        sender: sender,
        assetId: BigInt(assetId),
        ensureZeroBalance: true,
      });

      return {
        status: 'success',
        txid: result.txIds[0],
        message: `✅ Successfully opted out of asset ${assetId}`
      };

    } catch (error) {
      return {
        status: 'error',
        message: `❌ Opt-out failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private isValidAddress(address: string): boolean {
    // Simple Algorand address validation (58 characters, base32)
    const addressRegex = /^[A-Z2-7]{58}$/;
    return addressRegex.test(address);
  }
} 