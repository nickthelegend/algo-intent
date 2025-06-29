import { useWallet, Wallet, WalletId } from '@txnlab/use-wallet-react'
import Account from './Account'

interface ConnectWalletInterface {
  openModal: boolean
  closeModal: () => void
}

const ConnectWallet = ({ openModal, closeModal }: ConnectWalletInterface) => {
  const { wallets, activeAddress } = useWallet()

  const isKmd = (wallet: Wallet) => wallet.id === WalletId.KMD

  return (
    <div
      className={`modal ${openModal ? 'modal-open' : ''}`}
      style={{
        display: openModal ? 'flex' : 'none',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif',
      }}
    >
      <div
        className="modal-box"
        style={{
          borderRadius: '2.5rem',
          boxShadow: '0 8px 32px rgba(0,0,0,0.10)',
          background: '#fff',
          padding: '2.5rem 2.5rem 2rem 2.5rem',
          minWidth: 380,
          maxWidth: 440,
          width: '100%',
          position: 'relative',
        }}
      >
        <h3
          style={{
            fontWeight: 800,
            fontSize: '1.7rem',
            textAlign: 'center',
            marginBottom: '2.2rem',
            letterSpacing: '-1px',
            color: '#1a232b',
          }}
        >
          Select Wallet Provider
        </h3>
        <div style={{ display: 'flex', gap: '1.2rem', justifyContent: 'center', marginBottom: '2.2rem' }}>
          {!activeAddress &&
            wallets?.map((wallet) => (
              <button
                data-test-id={`${wallet.id}-connect`}
                key={`provider-${wallet.id}`}
                onClick={() => wallet.connect()}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: '#f6fcfd',
                  border: '2.5px solid #e0f7fa',
                  borderRadius: '1.5rem',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                  padding: '1.2rem 1.2rem 0.7rem 1.2rem',
                  minWidth: 90,
                  minHeight: 110,
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '1.08rem',
                  color: '#1a232b',
                  transition: 'border 0.2s, box-shadow 0.2s',
                }}
                onMouseOver={e => {
                  (e.currentTarget as HTMLButtonElement).style.border = '2.5px solid #4ecb6e';
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 4px 16px rgba(78,203,110,0.10)';
                }}
                onMouseOut={e => {
                  (e.currentTarget as HTMLButtonElement).style.border = '2.5px solid #e0f7fa';
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)';
                }}
              >
                {!isKmd(wallet) && (
                  <img
                    alt={`wallet_icon_${wallet.id}`}
                    src={wallet.metadata.icon}
                    style={{ width: 44, height: 44, objectFit: 'contain', marginBottom: 10 }}
                  />
                )}
                <span>{isKmd(wallet) ? 'LocalNet' : wallet.metadata.name}</span>
              </button>
            ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button
            data-test-id="close-wallet-modal"
            className="wallet-connect-btn"
            style={{
              background: '#f6fcfd',
              color: '#1a232b',
              border: '1.5px solid #e0f7fa',
              borderRadius: '1.25rem',
              padding: '0.8rem 2.2rem',
              fontWeight: 700,
              fontSize: '1.08rem',
              cursor: 'pointer',
              boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
              fontFamily: 'inherit',
              marginTop: 0,
            }}
            onClick={closeModal}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
export default ConnectWallet
