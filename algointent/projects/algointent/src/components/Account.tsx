import { useWallet } from '@txnlab/use-wallet-react'
import { useMemo } from 'react'
import { ellipseAddress } from '../utils/ellipseAddress'
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs'

const Account = () => {
  const { activeAddress } = useWallet()
  const algoConfig = getAlgodConfigFromViteEnvironment()

  const networkName = useMemo(() => {
    return algoConfig.network === '' ? 'localnet' : algoConfig.network.toLocaleLowerCase()
  }, [algoConfig.network])

  return (
    <div className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-lg border border-green-200">
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="font-medium text-gray-700">Connected Wallet</span>
        </div>
        <a 
          className="block text-blue-600 hover:text-blue-800 font-mono text-sm break-all transition-colors" 
          target="_blank" 
          href={`https://lora.algokit.io/${networkName}/account/${activeAddress}/`}
          rel="noopener noreferrer"
        >
          {ellipseAddress(activeAddress)}
        </a>
        <div className="text-sm text-gray-600">
          Network: <span className="font-medium capitalize">{networkName}</span>
        </div>
      </div>
    </div>
  )
}

export default Account
