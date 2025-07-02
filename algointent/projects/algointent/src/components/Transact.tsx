import { algo, AlgorandClient } from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet-react'
import { useSnackbar } from 'notistack'
import { useState } from 'react'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'

interface TransactInterface {
  openModal: boolean
  setModalState: (value: boolean) => void
}

const Transact = ({ openModal, setModalState }: TransactInterface) => {
  const [loading, setLoading] = useState<boolean>(false)
  const [receiverAddress, setReceiverAddress] = useState<string>('')

  const algodConfig = getAlgodConfigFromViteEnvironment()
  const algorand = AlgorandClient.fromConfig({ algodConfig })

  const { enqueueSnackbar } = useSnackbar()

  const { transactionSigner, activeAddress } = useWallet()

  const handleSubmitAlgo = async () => {
    setLoading(true)

    if (!transactionSigner || !activeAddress) {
      enqueueSnackbar('Please connect wallet first', { variant: 'warning' })
      return
    }

    try {
      enqueueSnackbar('Sending transaction...', { variant: 'info' })
      const result = await algorand.send.payment({
        signer: transactionSigner,
        sender: activeAddress,
        receiver: receiverAddress,
        amount: algo(1),
      })
      enqueueSnackbar(`Transaction sent: ${result.txIds[0]}`, { variant: 'success' })
      setReceiverAddress('')
    } catch (e) {
      enqueueSnackbar('Failed to send transaction', { variant: 'error' })
    }

    setLoading(false)
  }

  return (
    <div className={`modal ${openModal ? 'modal-open' : ''}`} style={{ display: openModal ? 'block' : 'none' }}>
      <div className="modal-box">
        <h3 className="font-bold text-2xl mb-4">Send Payment Transaction</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Receiver Address
            </label>
            <input
              type="text"
              data-test-id="receiver-address"
              placeholder="Enter wallet address (58 characters)"
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
              value={receiverAddress}
              onChange={(e) => {
                setReceiverAddress(e.target.value)
              }}
            />
            <p className="text-xs text-gray-500 mt-1">
              This will send 1 ALGO to the specified address
            </p>
          </div>
        </div>

        <div className="modal-action">
          <button 
            className="btn" 
            onClick={() => setModalState(!openModal)}
          >
            Close
          </button>
          <button
            data-test-id="send-algo"
            className={`btn ${receiverAddress.length === 58 ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700' : 'bg-gray-300 cursor-not-allowed'} text-white font-medium px-6 py-3 rounded-lg transition-all duration-200`}
            onClick={handleSubmitAlgo}
            disabled={receiverAddress.length !== 58 || loading}
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="loading-spinner"></div>
                <span>Sending...</span>
              </div>
            ) : (
              'Send 1 ALGO'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Transact