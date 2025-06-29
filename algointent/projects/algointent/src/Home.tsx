// src/components/Home.tsx
import React from 'react';
import WalletConnectButton from './components/WalletConnectButton';
import AlgoIntentChat from './components/AlgoIntentChat';
import logo from './assets/logo.svg';

const Home: React.FC = () => {
  return (
    <div className="main-container min-h-screen flex flex-col bg-[#f8fafc]" style={{ minHeight: '100vh', width: '100vw' }}>
      {/* Spacer for wallet button on mobile */}
      <div className="header-spacer"></div>
      {/* Header/title centered at the top */}
      <div style={{ width: '100%', textAlign: 'center', marginTop: '5rem', marginBottom: '2.5rem' }}>
        <h1 style={{ fontWeight: 800, fontSize: '2.3rem', letterSpacing: '-1px', color: '#1a232b', margin: 0 }}>Algo-Intent Chat</h1>
        <div style={{ fontSize: '1.15rem', color: '#7a8a99', fontWeight: 500, marginTop: '0.5rem' }}>AI-powered Algorand wallet assistant</div>
      </div>
      {/* Main chat area, full width, flat */}
      <div style={{ flex: 1, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-end' }}>
        <div style={{ width: '100%', maxWidth: 720, margin: '0 auto', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
          <AlgoIntentChat />
        </div>
      </div>
      {/* Wallet connect button at top right (all screens) */}
      <div className="wallet-connect-top-right">
        <WalletConnectButton />
      </div>
    </div>
  );
};

export default Home;
