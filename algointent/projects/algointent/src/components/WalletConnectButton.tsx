import React, { useState, useRef, useEffect } from 'react';
import { useWallet } from '@txnlab/use-wallet-react';
import { ellipseAddress } from '../utils/ellipseAddress';
import ConnectWallet from './ConnectWallet';

const WalletConnectButton: React.FC = () => {
  const { wallets, activeAddress } = useWallet();
  const [menuOpen, setMenuOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        !buttonRef.current?.contains(event.target as Node)
      ) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [menuOpen]);

  const handleConnect = () => {
    setModalOpen(true);
  };

  const handleDisconnect = async () => {
    if (wallets) {
      const activeWallet = wallets.find((w) => w.isActive);
      if (activeWallet) {
        await activeWallet.disconnect();
      } else {
        localStorage.removeItem('@txnlab/use-wallet:v3');
        window.location.reload();
      }
    }
    setMenuOpen(false);
  };

  return (
    <div style={{ position: 'relative', zIndex: 100 }}>
      {!activeAddress ? (
        <>
          <button className="wallet-connect-btn" onClick={handleConnect} ref={buttonRef}>
            Connect Wallet
          </button>
          <ConnectWallet openModal={modalOpen} closeModal={() => setModalOpen(false)} />
        </>
      ) : (
        <button
          className="wallet-connect-btn connected flex items-center gap-2"
          onClick={() => setMenuOpen((open) => !open)}
          ref={buttonRef}
        >
          <span style={{ display: 'flex', alignItems: 'center' }}>
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" fill="#fff" stroke="#4ecb6e" strokeWidth="2"/><ellipse cx="12" cy="17" rx="7" ry="4" fill="#fff" stroke="#4ecb6e" strokeWidth="2"/></svg>
          </span>
          <span style={{ fontWeight: 600 }}>{ellipseAddress(activeAddress)}</span>
        </button>
      )}
      {menuOpen && activeAddress && (
        <div
          ref={menuRef}
          style={{
            position: 'absolute',
            right: 0,
            marginTop: '0.5rem',
            background: '#fff',
            border: '1.5px solid #4ecb6e',
            borderRadius: '1rem',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            zIndex: 1000,
            minWidth: '160px',
          }}
        >
          <button
            className="wallet-connect-btn"
            style={{ width: '100%', border: 'none', borderRadius: '1rem', background: 'none', color: '#1a232b', fontWeight: 600, padding: '0.8rem' }}
            onClick={handleDisconnect}
          >
            Disconnect
          </button>
        </div>
      )}
    </div>
  );
};

export default WalletConnectButton; 