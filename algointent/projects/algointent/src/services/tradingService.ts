import tinyman from '@tinymanorg/tinyman-js-sdk';
import algosdk from 'algosdk';

export interface TradingResult {
  status: 'success' | 'error' | 'pending';
  txid?: string;
  message: string;
  error?: string;
  data?: any;
}

export interface PriceData {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  marketCap: number;
  lastUpdated: string;
}

export interface SwapQuote {
  fromAsset: string;
  toAsset: string;
  fromAmount: number;
  toAmount: number;
  priceImpact: number;
  fee: number;
  route: string[];
}

export interface LimitOrder {
  id: string;
  fromAsset: string;
  toAsset: string;
  amount: number;
  price: number;
  type: 'buy' | 'sell';
  status: 'pending' | 'filled' | 'cancelled';
  createdAt: Date;
}

const COINGECKO_IDS: Record<string, string> = {
  'ALGO': 'algorand',
  'USDC': 'usd-coin',
  'TINYUSDC': 'usd-coin', // for testnet TinyUSDC, use usd-coin for price reference
  // add more as needed
};

const TINYUSDC_ID = 21582668; // Testnet TinyUSDC ASA ID

// Testnet asset IDs
const TESTNET_ASA_IDS: Record<string, number> = {
  'ALGO': 0,
  'USDC': 10458941 // Real USDC on testnet
};

function resolveTestnetAssetId(symbolOrId: string): number {
  if (/^\d+$/.test(symbolOrId)) return Number(symbolOrId);
  return TESTNET_ASA_IDS[symbolOrId.toUpperCase()] ?? Number(symbolOrId);
}

const { poolUtils, SwapType, Swap } = tinyman;
const algodClient = new algosdk.Algodv2('', 'https://testnet-api.algonode.cloud', '');

// Tinyman-compatible signer for use-wallet-react
export async function tinymanSigner(txns: any[], signTransactions: (txns: Uint8Array[]) => Promise<(Uint8Array | null)[]>) {
  // Find which txns need to be signed by the user
  const indexesToSign = txns
    .map((txn, idx) => (txn.signers && txn.signers.length > 0 ? idx : null))
    .filter(idx => idx !== null);
  const txnBlobs = txns.map(txn => algosdk.encodeUnsignedTransaction(txn.txn));
  // Sign only the required txns, filter out nulls
  const signed = indexesToSign.length > 0 ? (await signTransactions(indexesToSign.map(idx => txnBlobs[idx]))).filter(Boolean) : [];
  // Reconstruct the group: signed user txns, LogicSig txns as-is
  let signedIdx = 0;
  const result = txns.map((txn, idx) => {
    if (txn.signers && txn.signers.length > 0) {
      return signed[signedIdx++];
    } else if (txn.lsig) {
      return algosdk.signLogicSigTransactionObject(txn.txn, txn.lsig).blob;
    } else {
      // Should not happen
      return txnBlobs[idx];
    }
  });
  return result;
}

export class TradingService {
  private apiKey: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = import.meta.env.VITE_COINGECKO_API_KEY || '';
    this.baseUrl = 'https://api.coingecko.com/api/v3';
  }

  // Get current market prices
  async getPrice(symbol: string): Promise<PriceData | null> {
    const id = COINGECKO_IDS[symbol.toUpperCase()] || symbol.toLowerCase();
    try {
      const response = await fetch(
        `${this.baseUrl}/simple/price?ids=${id}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true&include_last_updated_at=true`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const assetData = data[id];

      if (!assetData) {
        return null;
      }

      return {
        symbol: symbol.toUpperCase(),
        price: assetData.usd,
        change24h: assetData.usd_24h_change,
        volume24h: assetData.usd_24h_vol,
        marketCap: assetData.usd_market_cap,
        lastUpdated: new Date(assetData.last_updated_at * 1000).toISOString()
      };
    } catch (error) {
      console.error('Error fetching price:', error);
      return null;
    }
  }

  // Get multiple asset prices
  async getPrices(symbols: string[]): Promise<PriceData[]> {
    const ids = symbols.map(s => COINGECKO_IDS[s.toUpperCase()] || s.toLowerCase()).join(',');
    try {
      const response = await fetch(
        `${this.baseUrl}/simple/price?ids=${ids}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true&include_last_updated_at=true`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const results: PriceData[] = [];

      for (const symbol of symbols) {
        const id = COINGECKO_IDS[symbol.toUpperCase()] || symbol.toLowerCase();
        const assetData = data[id];
        if (assetData) {
          results.push({
            symbol: symbol.toUpperCase(),
            price: assetData.usd,
            change24h: assetData.usd_24h_change,
            volume24h: assetData.usd_24h_vol,
            marketCap: assetData.usd_market_cap,
            lastUpdated: new Date(assetData.last_updated_at * 1000).toISOString()
          });
        }
      }

      return results;
    } catch (error) {
      console.error('Error fetching prices:', error);
      return [];
    }
  }

  // Get market information
  async getMarketInfo(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/global`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Error fetching market info:', error);
      return null;
    }
  }

  // Simulate a swap quote (this would integrate with actual DEX APIs)
  async getSwapQuote(
    fromAsset: string,
    toAsset: string,
    amount: number
  ): Promise<SwapQuote | null> {
    const fromId = COINGECKO_IDS[fromAsset.toUpperCase()] || fromAsset.toLowerCase();
    const toId = COINGECKO_IDS[toAsset.toUpperCase()] || toAsset.toLowerCase();
    try {
      // This is a simulation - in a real implementation, you'd call DEX APIs
      // like Tinyman, Pact, or other Algorand DEXes
      
      // Get current prices to calculate the quote
      const prices = await this.getPrices([fromAsset, toAsset]);
      const fromPrice = prices.find(p => p.symbol === fromAsset.toUpperCase())?.price || 0;
      const toPrice = prices.find(p => p.symbol === toAsset.toUpperCase())?.price || 0;

      if (fromPrice === 0 || toPrice === 0) {
        return null;
      }

      const fromValue = amount * fromPrice;
      const toAmount = fromValue / toPrice;
      const priceImpact = 0.5; // Simulated 0.5% price impact
      const fee = fromValue * 0.003; // Simulated 0.3% fee

      return {
        fromAsset: fromAsset.toUpperCase(),
        toAsset: toAsset.toUpperCase(),
        fromAmount: amount,
        toAmount: toAmount * (1 - priceImpact / 100),
        priceImpact,
        fee,
        route: [fromAsset.toUpperCase(), toAsset.toUpperCase()]
      };
    } catch (error) {
      console.error('Error getting swap quote:', error);
      return null;
    }
  }

  /**
   * Executes a swap using the Tinyman v2 SDK and smart contracts on Algorand testnet.
   * All transactions are constructed, signed, and submitted via the official Tinyman protocol.
   * No manual transaction construction is used.
   */
  async executeSwap(
    fromAsset: string,
    toAsset: string,
    amount: number,
    signer: any,
    sender: string,
    signTransactions?: (txns: Uint8Array[]) => Promise<(Uint8Array | null)[]>
  ): Promise<TradingResult> {
    try {
      const assetInId = resolveTestnetAssetId(fromAsset);
      const assetOutId = resolveTestnetAssetId(toAsset);
      console.log('Tinyman swap asset IDs:', { assetInId, assetOutId });
      if (isNaN(assetInId) || isNaN(assetOutId)) {
        return {
          status: 'error',
          message: '❌ Invalid asset symbol or ID.',
          error: 'Invalid asset'
        };
      }
      // Fetch decimals for both assets (ALGO is always 6)
      const assetInDecimals = assetInId === 0 ? 6 : await this.getAssetDecimals(assetInId);
      const assetOutDecimals = assetOutId === 0 ? 6 : await this.getAssetDecimals(assetOutId);
      const assetIn = { id: assetInId, decimals: assetInDecimals };
      const assetOut = { id: assetOutId, decimals: assetOutDecimals };
      const assetInAmount = { ...assetIn, amount: BigInt(Math.floor(amount * 10 ** assetInDecimals)) };
      console.log('Tinyman swap assetIn:', assetIn, 'assetOut:', assetOut, 'amount:', assetInAmount.amount.toString());

      // 1. Fetch pool (Tinyman SDK)
      const pool = await poolUtils.v2.getPoolInfo({
        client: algodClient,
        network: 'testnet',
        asset1ID: assetIn.id,
        asset2ID: assetOut.id
      });
      console.log('Tinyman pool:', pool);
      if (!pool) {
        return {
          status: 'error',
          message: '❌ Could not find Tinyman pool for this asset pair on testnet.',
          error: 'No pool'
        };
      }

      // 2. Get quote (Tinyman SDK)
      const quote = await Swap.v2.getQuote({
        type: SwapType.FixedInput,
        amount: assetInAmount.amount,
        assetIn,
        assetOut,
        pool,
        network: 'testnet',
        slippage: 0.01
      });
      console.log('Tinyman quote:', quote);
      if (!quote) {
        return {
          status: 'error',
          message: '❌ Could not get swap quote. Pool may not exist or insufficient liquidity.',
          error: 'No quote'
        };
      }

      // 3. Generate transactions (Tinyman SDK)
      const txns = await Swap.v2.generateTxns({
        client: algodClient,
        network: 'testnet',
        quote,
        swapType: SwapType.FixedInput,
        slippage: 0.01,
        initiatorAddr: sender
      });
      console.log('Tinyman txns:', txns);

      // 4. Sign transactions (robust Tinyman-compatible signer)
      let signedTxns;
      if (signTransactions) {
        signedTxns = await tinymanSigner(txns, signTransactions);
      } else {
        signedTxns = await signer(txns);
      }
      console.log('Tinyman signedTxns:', signedTxns);

      // 5. Execute (Tinyman SDK)
      const result = await Swap.v2.execute({
        client: algodClient,
        quote,
        txGroup: txns,
        signedTxns
      });

      // Output amount for direct swap: quote.data.quote.assetOutAmount (scale by decimals!)
      let outputAmount = 0;
      if (quote.data && 'quote' in quote.data && quote.data.quote.assetOutAmount) {
        outputAmount = Number(quote.data.quote.assetOutAmount) / Math.pow(10, assetOutDecimals);
      }

      return {
        status: 'success',
        txid: result.txnID,
        message: `✅ Tinyman swap successful! ${amount} ${fromAsset} → ${outputAmount} ${toAsset}. TxID: ${result.txnID}`,
        data: quote
      };
    } catch (error: any) {
      console.error('Tinyman swap error:', error);
      return {
        status: 'error',
        message: `❌ Tinyman swap failed: ${error?.message || error}`,
        error: error?.message || String(error)
      };
    }
  }

  // Helper to fetch decimals for an ASA
  async getAssetDecimals(assetId: number): Promise<number> {
    if (assetId === 0) return 6;
    // Use Algorand Indexer or Algod to fetch asset params
    const algod = new algosdk.Algodv2('', 'https://testnet-api.algonode.cloud', '');
    const assetInfo = await algod.getAssetByID(assetId).do();
    return assetInfo.params.decimals;
  }

  // Set a limit order (simulated)
  async setLimitOrder(
    fromAsset: string,
    toAsset: string,
    amount: number,
    price: number,
    type: 'buy' | 'sell',
    signer: any,
    sender: string
  ): Promise<TradingResult> {
    try {
      // In a real implementation, this would:
      // 1. Create a limit order smart contract call
      // 2. Build the transaction
      // 3. Sign and submit
      // 4. Store the order in a database

      const orderId = `limit_${Date.now()}`;
      
      return {
        status: 'success',
        txid: orderId,
        message: `✅ Limit order set successfully! ${type.toUpperCase()} ${amount} ${fromAsset} at $${price} ${toAsset}. Order ID: ${orderId}`,
        data: {
          orderId,
          fromAsset,
          toAsset,
          amount,
          price,
          type,
          status: 'pending'
        }
      };
    } catch (error) {
      return {
        status: 'error',
        message: `❌ Failed to set limit order: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  // Set a stop-loss order (simulated)
  async setStopLoss(
    asset: string,
    amount: number,
    triggerPrice: number,
    signer: any,
    sender: string
  ): Promise<TradingResult> {
    try {
      const orderId = `stop_loss_${Date.now()}`;
      
      return {
        status: 'success',
        txid: orderId,
        message: `✅ Stop-loss order set successfully! Sell ${amount} ${asset} when price drops to $${triggerPrice}. Order ID: ${orderId}`,
        data: {
          orderId,
          asset,
          amount,
          triggerPrice,
          type: 'stop_loss',
          status: 'pending'
        }
      };
    } catch (error) {
      return {
        status: 'error',
        message: `❌ Failed to set stop-loss: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  // Get user's active orders (simulated)
  async getActiveOrders(sender: string): Promise<LimitOrder[]> {
    // In a real implementation, this would fetch from a database
    return [];
  }

  // Cancel an order (simulated)
  async cancelOrder(orderId: string, signer: any, sender: string): Promise<TradingResult> {
    try {
      return {
        status: 'success',
        txid: `cancel_${orderId}`,
        message: `✅ Order ${orderId} cancelled successfully!`
      };
    } catch (error) {
      return {
        status: 'error',
        message: `❌ Failed to cancel order: ${error instanceof Error ? error.message : 'Unknown error'}`,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

export const tradingService = new TradingService(); 