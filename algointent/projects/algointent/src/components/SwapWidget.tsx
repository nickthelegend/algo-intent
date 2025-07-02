import React, { useEffect, useState } from 'react';
import { useWallet } from '@txnlab/use-wallet-react';
import { TradingService } from '../services/tradingService';

interface SwapWidgetProps {
  fromAsset?: string;
  toAsset?: string;
  amount?: number;
  onSwapCompleted?: (result: any) => void;
  onSwapFailed?: (error: any) => void;
}

const TESTNET_ASSETS = [
  { symbol: 'ALGO', id: 0, decimals: 6, name: 'Algorand', icon: 'https://cryptologos.cc/logos/algorand-algo-logo.png?v=026' },
  { symbol: 'USDC', id: 10458941, decimals: 6, name: 'USDC', icon: 'https://cryptologos.cc/logos/usd-coin-usdc-logo.png?v=026' },
];

const getAssetMeta = (symbol: string) => TESTNET_ASSETS.find(a => a.symbol === symbol) || TESTNET_ASSETS[0];

const tradingService = new TradingService();

const SwapWidget: React.FC<SwapWidgetProps> = ({ fromAsset, toAsset, amount, onSwapCompleted, onSwapFailed }) => {
  const { activeAddress, signTransactions, transactionSigner } = useWallet();
  const [from, setFrom] = useState(fromAsset || 'ALGO');
  const [to, setTo] = useState(toAsset || 'USDC');
  const [amt, setAmt] = useState(amount || 1);
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [swapResult, setSwapResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [fromUsd, setFromUsd] = useState<number | null>(null);
  const [toUsd, setToUsd] = useState<number | null>(null);

  // Fetch quote and USD values when from/to/amt changes
  useEffect(() => {
    let cancelled = false;
    setQuote(null);
    setError(null);
    setFromUsd(null);
    setToUsd(null);
    if (!from || !to || !amt || isNaN(amt) || amt <= 0) return;
    setLoading(true);
    Promise.all([
      tradingService.getSwapQuote(from, to, amt),
      tradingService.getPrices([from, to])
    ])
      .then(([q, prices]) => {
        if (!cancelled) {
          setQuote(q);
          const fromPrice = prices.find(p => p.symbol === from)?.price;
          const toPrice = prices.find(p => p.symbol === to)?.price;
          setFromUsd(fromPrice ? amt * fromPrice : null);
          setToUsd(toPrice && q?.toAmount ? q.toAmount * toPrice : null);
        }
      })
      .catch(e => {
        if (!cancelled) setError('Could not fetch quote');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [from, to, amt]);

  const handleSwap = async () => {
    setLoading(true);
    setError(null);
    setSwapResult(null);
    try {
      const result = await tradingService.executeSwap(
        from,
        to,
        amt,
        transactionSigner,
        activeAddress!,
        signTransactions
      );
      setSwapResult(result);
      if (result.status === 'success') {
        onSwapCompleted?.(result);
      } else {
        setError(result.message);
        onSwapFailed?.(result);
      }
    } catch (e: any) {
      setError(e?.message || 'Swap failed');
      onSwapFailed?.(e);
    } finally {
      setLoading(false);
    }
  };

  // Swap from/to assets
  const handleSwitch = () => {
    setFrom(to);
    setTo(from);
    setQuote(null);
    setFromUsd(null);
    setToUsd(null);
  };

  const fromMeta = getAssetMeta(from);
  const toMeta = getAssetMeta(to);

  return (
    <div style={{
      minWidth: 320,
      maxWidth: 420,
      width: '100%',
      background: '#fff',
      borderRadius: 24,
      boxShadow: '0 8px 32px rgba(0,0,0,0.10)',
      padding: '2.2rem 2rem 1.5rem 2rem',
      margin: '0 auto',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif',
    }}>
      <div style={{ fontWeight: 800, fontSize: '1.7rem', marginBottom: '2rem', letterSpacing: '-1px', color: '#1a232b', textAlign: 'center' }}>
        Swap Tokens
      </div>
      {/* FROM FIELD */}
      <div style={{
        width: '100%',
        background: '#f6fcfd',
        borderRadius: '1.5rem',
        border: '1.5px solid #e0f7fa',
        padding: '1.2rem 1.3rem 0.7rem 1.3rem',
        marginBottom: '0.7rem',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
          <span style={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            background: from === 'ALGO' ? '#4ecb6e' : '#2563eb',
            color: '#fff',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '1.1rem',
            marginRight: 10
          }}>{fromMeta.symbol[0]}</span>
          <span style={{ fontWeight: 700, fontSize: '1.08rem', color: '#1a232b', marginRight: 6 }}>{fromMeta.name}</span>
          <span style={{ fontWeight: 600, fontSize: '1.01rem', color: '#7a8a99' }}>{fromMeta.symbol}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <input
            type="number"
            min={0}
            value={amt}
            onChange={e => setAmt(Number(e.target.value))}
            style={{
              border: 'none',
              background: 'transparent',
              fontWeight: 800,
              fontSize: '2.1rem',
              color: '#1a232b',
              outline: 'none',
              width: '70%',
            }}
            placeholder="0.00"
          />
          <div style={{ textAlign: 'right', color: '#7a8a99', fontWeight: 600, fontSize: '1.08rem', marginBottom: 2 }}>
            {fromUsd !== null ? `≈ $${fromUsd.toFixed(2)}` : ''}
          </div>
        </div>
      </div>
      {/* SWITCH BUTTON */}
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: '50%',
          background: '#fff',
          border: '2px solid #e5e7eb',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '-1.2rem 0',
          cursor: 'pointer',
          zIndex: 2,
        }}
        onClick={handleSwitch}
        title="Switch"
      >
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
          <g stroke="#888" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 7V21" />
            <path d="M10 11L14 7L18 11" />
            <path d="M18 17L14 21L10 17" />
          </g>
        </svg>
      </div>
      {/* TO FIELD */}
      <div style={{
        width: '100%',
        background: '#f6fcfd',
        borderRadius: '1.5rem',
        border: '1.5px solid #e0f7fa',
        padding: '1.2rem 1.3rem 0.7rem 1.3rem',
        marginBottom: '1.2rem',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
          <span style={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            background: to === 'ALGO' ? '#4ecb6e' : '#2563eb',
            color: '#fff',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '1.1rem',
            marginRight: 10
          }}>{toMeta.symbol[0]}</span>
          <span style={{ fontWeight: 700, fontSize: '1.08rem', color: '#1a232b', marginRight: 6 }}>{toMeta.name}</span>
          <span style={{ fontWeight: 600, fontSize: '1.01rem', color: '#7a8a99' }}>{toMeta.symbol}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
          <input
            type="text"
            value={quote && quote.toAmount ? quote.toAmount.toFixed(6) : ''}
            readOnly
            style={{
              border: 'none',
              background: 'transparent',
              fontWeight: 800,
              fontSize: '2.1rem',
              color: '#1a232b',
              outline: 'none',
              width: '70%',
            }}
            placeholder="0.00"
          />
          <div style={{ textAlign: 'right', color: '#7a8a99', fontWeight: 600, fontSize: '1.08rem', marginBottom: 2 }}>
            {quote && quote.toAmount && toUsd !== null ? `≈ $${toUsd.toFixed(2)}` : ''}
          </div>
        </div>
      </div>
      {/* Price Impact and Fee (below fields) */}
      {quote && (
        <div style={{ width: '100%', marginBottom: 12, color: '#7a8a99', fontWeight: 600, fontSize: '1.01rem', textAlign: 'right' }}>
          Fee: <span style={{ color: '#1a232b', fontWeight: 700 }}>{quote.fee}</span>
        </div>
      )}
      <button
        onClick={handleSwap}
        disabled={loading || !activeAddress || !from || !to || !amt || from === to}
        style={{ width: '100%', padding: '1.1rem', borderRadius: '1.2rem', background: '#4ecb6e', color: '#fff', fontWeight: 800, fontSize: '1.15rem', border: 'none', cursor: loading ? 'not-allowed' : 'pointer', marginTop: 4, marginBottom: 2, boxShadow: '0 2px 8px rgba(78,203,110,0.10)', opacity: loading || !activeAddress || from === to ? 0.6 : 1 }}
      >
        Swap
      </button>
      {error && <div style={{ color: '#b91c1c', marginTop: 14, width: '100%', textAlign: 'center', fontWeight: 600 }}>{error}</div>}
      {swapResult && swapResult.status === 'success' && (
        <div style={{ color: '#10b981', marginTop: 14, width: '100%', textAlign: 'center', fontWeight: 600 }}>
          Swap successful! <a href={`https://testnet.explorer.perawallet.app/tx/${swapResult.txid}`} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', textDecoration: 'underline' }}>View on Explorer</a>
        </div>
      )}
      {!activeAddress && <div style={{ color: '#b91c1c', marginTop: 12, textAlign: 'center', fontWeight: 500, fontSize: '1.01rem' }}>Connect your wallet to swap</div>}
    </div>
  );
};

export default SwapWidget; 