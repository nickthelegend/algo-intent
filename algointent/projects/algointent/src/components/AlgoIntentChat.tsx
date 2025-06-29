import React, { useState, useRef, useEffect } from 'react';
import { useWallet } from '@txnlab/use-wallet-react';
import { useSnackbar } from 'notistack';
import { WidgetController } from '@tinymanorg/tinyman-swap-widget-sdk';
import { aiIntentService, ParsedIntent } from '../services/aiIntentService';
import { TransactionService, NFTMetadata } from '../services/transactionService';
import { tradingService, tinymanSigner } from '../services/tradingService';
import { ipfsService } from '../services/ipfsService';
import { getAlgodConfigFromViteEnvironment } from '../utils/network/getAlgoClientConfigs';
import logo from '../assets/logo.svg';
import SwapWidget from './SwapWidget';
import algosdk from 'algosdk';

interface ChatMessage {
  id: string;
  type: 'user' | 'bot' | 'widget';
  content: string;
  timestamp: Date;
  status?: 'pending' | 'success' | 'error';
  txid?: string;
  imageUrl?: string;
  isPendingImage?: boolean;
  widgetParams?: {
    fromAsset?: string;
    toAsset?: string;
    amount?: number;
  };
}

interface PendingImage {
  file: File;
  preview: string;
  timestamp: Date;
}

// Add this at the top, outside the component
let messageCounter = 0;

// TinymanSwapWidget using the official SDK
const TinymanSwapWidget: React.FC<{
  accountAddress: string;
  fromAsset?: string;
  toAsset?: string;
  amount?: number;
  onSwapCompleted?: (data: any) => void;
  onSwapFailed?: (data: any) => void;
}> = ({ accountAddress, fromAsset, toAsset, amount, onSwapCompleted, onSwapFailed }) => {
  const widgetRef = useRef<HTMLDivElement>(null);
  const [widgetController, setWidgetController] = useState<WidgetController | null>(null);
  // Access wallet context for signing
  const { signTransactions } = useWallet();

  useEffect(() => {
    if (widgetRef.current && accountAddress) {
      // Create widget options
      const widgetOptions = {
        accountAddress,
        network: 'testnet',
        useParentSigner: true, // Enable parent signer bridge
        parentUrlOrigin: window.location.origin,
        ...(fromAsset && { fromAsset }),
        ...(toAsset && { toAsset }),
        ...(amount && { amount: amount.toString() }),
      };

      const widgetUrl = WidgetController.generateWidgetIframeUrl(widgetOptions);
      const iframe = document.createElement('iframe');
      iframe.src = widgetUrl;
      iframe.style.width = '100%';
      iframe.style.height = '500px';
      iframe.style.border = 'none';
      iframe.style.borderRadius = '16px';
      iframe.title = 'Tinyman Swap Widget';

      if (widgetRef.current) {
        widgetRef.current.innerHTML = '';
        widgetRef.current.appendChild(iframe);
      }

      const controller = new WidgetController({
        iframe,
        accountAddress,
        network: 'testnet',
      });
      controller.addWidgetEventListeners();

      // Parent signer bridge
      const handleWidgetMessage = async (event: MessageEvent) => {
        if (event.origin !== 'https://app.tinyman.org') return;
        const { type, data, id } = event.data;
        if (type === 'SIGN_TRANSACTIONS') {
          try {
            // signTransactions expects an array of base64 encoded transactions
            const signed = await signTransactions(data.transactions);
            // Respond to the widget with the signed transactions
            iframe.contentWindow?.postMessage({
              type: 'SIGN_TRANSACTIONS_RESPONSE',
              id,
              data: { signedTransactions: signed },
            }, 'https://app.tinyman.org');
          } catch (err) {
            iframe.contentWindow?.postMessage({
              type: 'SIGN_TRANSACTIONS_RESPONSE',
              id,
              error: err instanceof Error ? err.message : 'Signing failed',
            }, 'https://app.tinyman.org');
          }
        } else {
          // Handle other widget events
          const { type, data } = event.data;
          switch (type) {
            case 'WIDGET_READY':
              break;
            case 'SWAP_COMPLETED':
              onSwapCompleted?.(data);
              break;
            case 'SWAP_FAILED':
              onSwapFailed?.(data);
              break;
          }
        }
      };
      window.addEventListener('message', handleWidgetMessage);
      setWidgetController(controller);
      return () => {
        window.removeEventListener('message', handleWidgetMessage);
        if (controller) {
          controller.removeWidgetEventListeners();
        }
      };
    }
    return undefined;
  }, [accountAddress, fromAsset, toAsset, amount, onSwapCompleted, onSwapFailed, signTransactions]);

  return (
    <div style={{ minWidth: 350, maxWidth: 420, width: '100%' }}>
      <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 8 }}>
        Swap Tokens {fromAsset && toAsset && amount ? `(${amount} ${fromAsset} → ${toAsset})` : ''}
      </div>
      <div ref={widgetRef} style={{ minHeight: '500px' }} />
    </div>
  );
};

const AlgoIntentChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [accountInfo, setAccountInfo] = useState<{ algo: number; assets: any[] }>({ algo: 0, assets: [] });
  const [pendingImage, setPendingImage] = useState<PendingImage | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { activeAddress, transactionSigner, signTransactions } = useWallet();
  const { enqueueSnackbar } = useSnackbar();
  
  const algodConfig = getAlgodConfigFromViteEnvironment();
  const transactionService = new TransactionService(algodConfig);

  // Load pending image from session storage on mount
  useEffect(() => {
    const savedPendingImage = sessionStorage.getItem('pendingImage');
    if (savedPendingImage) {
      try {
        const parsed = JSON.parse(savedPendingImage);
        // Note: We can't restore the File object from session storage
        // So we'll just show a message that an image was previously uploaded
        addBotMessage('📸 You have a previously uploaded image ready for NFT creation. Upload a new image or type "create NFT" to use the existing one.');
      } catch (error) {
        console.error('Failed to parse pending image from session storage:', error);
      }
    }
  }, []);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    const container = messagesEndRef.current?.parentElement;
    if (!container) return;
    const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 10;
    if (isAtBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Add welcome message only once on first mount
  useEffect(() => {
    setMessages([
      {
        id: 'welcome',
        type: 'bot',
        content: `Welcome to Algo-Intent! 🤖\n\nI'm your intelligent Algorand assistant with deep knowledge of blockchain, DeFi, and trading!\n\nI can help you with:\n\n💼 WALLET OPERATIONS:\n• Send ALGO to addresses\n• Send ALGO to multiple addresses at once\n• Create and transfer NFTs\n• Upload images and create NFTs with them\n• Opt-in/out of assets\n• Check balances\n\n📈 TRADING OPERATIONS:\n• Swap tokens (ALGO/USDC, etc.)\n• Set limit orders\n• Set stop-loss orders\n• Check current market prices\n• Get market information\n\n🎓 EDUCATION & HELP:\n• Explain Algorand concepts\n• Explain DeFi and trading\n• Answer questions about blockchain\n• Provide helpful context and explanations\n\nJust type what you want to do in plain English! I understand natural language and can handle complex requests.`,
        timestamp: new Date(),
      },
    ]);
    // eslint-disable-next-line
  }, []);

  // Fetch balance on wallet connect and after transactions
  useEffect(() => {
    const fetchBalance = async () => {
      if (activeAddress) {
        try {
          const info = await transactionService.getAccountBalance(activeAddress);
          setAccountInfo(info);
        } catch (error) {
          enqueueSnackbar('Failed to fetch balance', { variant: 'error' });
        }
      }
    };
    fetchBalance();
  }, [activeAddress]);

  const addMessage = (type: 'user' | 'bot', content: string, status?: 'pending' | 'success' | 'error', txid?: string, imageUrl?: string, isPendingImage?: boolean) => {
    const newMessage: ChatMessage = {
      id: `${Date.now()}-${messageCounter++}`,
      type,
      content,
      timestamp: new Date(),
      status,
      txid,
      imageUrl,
      isPendingImage
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const addBotMessage = (content: string, status?: 'pending' | 'success' | 'error', txid?: string) => {
    addMessage('bot', content, status, txid);
  };

  const addUserMessage = (content: string, imageUrl?: string) => {
    addMessage('user', content, undefined, undefined, imageUrl);
  };

  const generateUnitName = (name: string): string => {
    const initials = name.split(' ').map(word => word[0]).join('').toUpperCase();
    return initials.substring(0, 8) || 'NFT';
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        const preview = e.target?.result as string;
        setFilePreview(preview);
        
        // Store as pending image
        const pendingImageData: PendingImage = {
          file,
          preview,
          timestamp: new Date()
        };
        setPendingImage(pendingImageData);
        
        // Save to session storage
        sessionStorage.setItem('pendingImage', JSON.stringify({
          name: file.name,
          size: file.size,
          type: file.type,
          timestamp: new Date().toISOString()
        }));
        
        // Add message showing the uploaded image
        addUserMessage(`📸 Uploaded: ${file.name}`, preview);
        addBotMessage(`✅ Image uploaded successfully! You can now create an NFT with this image by typing "create NFT" or "create NFT named [name]".`);
      };
      reader.readAsDataURL(file);
    }
  };

  const clearPendingImage = () => {
    setPendingImage(null);
    sessionStorage.removeItem('pendingImage');
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() && !selectedFile) return;
    if (!activeAddress) {
      enqueueSnackbar('Please connect your wallet first', { variant: 'warning' });
      return;
    }

    const userInput = inputMessage.trim();
    
    // If there's a selected file, add it as a message first
    if (selectedFile && filePreview) {
      addUserMessage(`📸 Uploaded: ${selectedFile.name}`, filePreview);
    }
    
    addUserMessage(userInput);
    setIsProcessing(true);

    try {
      // Parse intent using AI
      const parsedIntent = await aiIntentService.parseIntent(userInput);
      
      if (!parsedIntent) {
        addBotMessage('❌ Sorry, I couldn\'t understand your request. Please try rephrasing it.');
        return;
      }

      // Handle different intents
      await handleIntent(parsedIntent, selectedFile || pendingImage?.file || null);
      
    } catch (error) {
      addBotMessage(`❌ Error processing your request: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
      setInputMessage('');
      setSelectedFile(null);
      setFilePreview(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Utility to sanitize AI output
  const sanitizeBotText = (text: string) => {
    if (!text) return '';
    // Remove markdown bold/italic (**text**, *text*, __text__, _text_)
    let sanitized = text.replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/__([^_]+)__/g, '$1')
      .replace(/_([^_]+)_/g, '$1');
    // Remove citation brackets like [1], [2], [3], [4]
    sanitized = sanitized.replace(/\[\d+\]/g, '');
    // Remove repeated whitespace
    sanitized = sanitized.replace(/\s{2,}/g, ' ');
    // Trim
    return sanitized.trim();
  };

  const handleIntent = async (intent: ParsedIntent, file: File | null) => {
    const { intent: action, parameters, context, explanation } = intent;

    // Always show explanation if present
    if (explanation) {
      addBotMessage(sanitizeBotText(explanation));
      // If the intent is not actionable, return early
      if ([
        'explain_algorand', 'explain_defi', 'explain_nft', 'explain_trading',
        'not_supported', 'general_help', 'unknown', undefined, null
      ].includes(action)) {
        return;
      }
    }

    // Handle trading operations
    if (action === 'trade_algo' || action === 'swap_tokens') {
      await handleSwapTokens(parameters);
      return;
    }

    if (action === 'set_limit_order') {
      await handleSetLimitOrder(parameters);
      return;
    }

    if (action === 'set_stop_loss') {
      await handleSetStopLoss(parameters);
      return;
    }

    if (action === 'check_prices' || action === 'market_info') {
      await handleCheckPrices(parameters);
      return;
    }

    // Handle existing wallet operations
    switch (action) {
      case 'send_algo':
        await handleSendAlgo(parameters);
        break;
      case 'create_nft':
        await handleCreateNFT(parameters, file);
        break;
      case 'create_nft_with_image':
        await handleCreateNFTWithImage(parameters, file);
        break;
      case 'send_nft':
        await handleSendNFT(parameters);
        break;
      case 'opt_in':
        await handleOptIn(parameters);
        break;
      case 'opt_out':
        await handleOptOut(parameters);
        break;
      case 'balance':
        await handleCheckBalance();
        break;
      default:
        if (explanation) {
          addBotMessage(explanation);
        } else {
          addBotMessage(`❌ I understand you want to ${action}, but this feature is not yet implemented.`);
        }
    }
  };

  const handleSendAlgo = async (parameters: any) => {
    if (!activeAddress || !algosdk.isValidAddress(activeAddress)) {
      addBotMessage('❌ Your wallet address is not valid. Please reconnect your wallet.');
      enqueueSnackbar('Invalid sender address', { variant: 'error' });
      return;
    }
    if (!parameters.amount || !parameters.recipient) {
      addBotMessage('❌ Missing amount or recipient address for ALGO transfer.');
      enqueueSnackbar('Missing amount or recipient address', { variant: 'error' });
      return;
    }
    addBotMessage(`🔄 Sending ${parameters.amount} ALGO to ${parameters.recipient}...`, 'pending');
    enqueueSnackbar('Sending ALGO...', { variant: 'info' });
    try {
      console.log('Using sender address:', activeAddress, 'Valid:', algosdk.isValidAddress(activeAddress), 'Length:', activeAddress.length);
      const result = await transactionService.sendAlgo(
        activeAddress,
        parameters.recipient,
        parameters.amount,
        transactionSigner!
      );
      await updateBalance();
      if (result.status === 'success') {
        addBotMessage(result.message, 'success', result.txid);
        enqueueSnackbar('Transaction successful!', { variant: 'success' });
      } else {
        addBotMessage(result.message, 'error');
        enqueueSnackbar('Transaction failed', { variant: 'error' });
      }
    } catch (error) {
      addBotMessage(`❌ Failed to send ALGO: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      enqueueSnackbar('Transaction failed', { variant: 'error' });
    }
  };

  const isValidAlgorandAddress = (addr: string) => /^[A-Z2-7]{58}$/.test(addr);

  const handleCreateNFT = async (parameters: any, file: File | null) => {
    if (!parameters.name) {
      addBotMessage('❌ NFT name is required.');
      enqueueSnackbar('NFT name is required', { variant: 'error' });
      return;
    }
    addBotMessage(`🔄 Creating NFT "${parameters.name}"...`, 'pending');
    enqueueSnackbar('Creating NFT...', { variant: 'info' });
    try {
      let ipfsUrl = '';
      if (file) {
        const uploadResult = await ipfsService.uploadToIPFS(file);
        if (uploadResult.success) {
          ipfsUrl = uploadResult.ipfsUrl!;
          addBotMessage(`📤 File uploaded to IPFS: ${uploadResult.ipfsHash}`);
          enqueueSnackbar('File uploaded to IPFS', { variant: 'success' });
        } else {
          addBotMessage(`⚠️ File upload failed: ${uploadResult.error}. Creating NFT without media.`);
          enqueueSnackbar('File upload failed', { variant: 'warning' });
        }
      }
      const metadata: NFTMetadata = {
        name: parameters.name,
        unitName: generateUnitName(parameters.name),
        totalSupply: parameters.supply || 1,
        description: parameters.description || '',
        url: ipfsUrl
      };
      const result = await transactionService.createNFT(
        activeAddress!,
        metadata,
        transactionSigner!
      );
      await updateBalance();
      if (result.status === 'success') {
        addBotMessage(result.message, 'success', result.txid);
        enqueueSnackbar('NFT created successfully!', { variant: 'success' });
        // Clear pending image after successful creation
        clearPendingImage();
        // Auto-opt-in to the new asset
        if (result.txid && result.message.includes('Asset ID:')) {
          const assetIdMatch = result.message.match(/Asset ID: (\d+)/);
          if (assetIdMatch) {
            const assetId = Number(assetIdMatch[1]);
            addBotMessage(`🔄 Opting in to asset ${assetId}...`, 'pending');
            enqueueSnackbar('Opting in to new NFT...', { variant: 'info' });
            const optInResult = await transactionService.optInToAsset(
              activeAddress!,
              assetId,
              transactionSigner!
            );
            await updateBalance();
            if (optInResult.status === 'success') {
              addBotMessage(optInResult.message, 'success', optInResult.txid);
              enqueueSnackbar('Auto-opt-in successful!', { variant: 'success' });
            } else {
              addBotMessage(optInResult.message, 'error');
              enqueueSnackbar('Auto-opt-in failed', { variant: 'error' });
            }
          }
        }
      } else {
        addBotMessage(result.message, 'error');
        enqueueSnackbar('NFT creation failed', { variant: 'error' });
      }
    } catch (error) {
      addBotMessage(`❌ Failed to create NFT: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      enqueueSnackbar('NFT creation failed', { variant: 'error' });
    }
  };

  const handleCreateNFTWithImage = async (parameters: any, file: File | null) => {
    if (!file) {
      addBotMessage('❌ No image found. Please upload an image first.');
      enqueueSnackbar('No image found', { variant: 'error' });
      return;
    }

    const nftName = parameters.name || `NFT_${Date.now()}`;
    addBotMessage(`🔄 Creating NFT "${nftName}" with uploaded image...`, 'pending');
    enqueueSnackbar('Creating NFT with image...', { variant: 'info' });
    
    try {
      // Upload image to IPFS
      const uploadResult = await ipfsService.uploadToIPFS(file);
      if (!uploadResult.success) {
        addBotMessage(`❌ Image upload failed: ${uploadResult.error}`);
        enqueueSnackbar('Image upload failed', { variant: 'error' });
        return;
      }

      addBotMessage(`📤 Image uploaded to IPFS: ${uploadResult.ipfsHash}`);
      enqueueSnackbar('Image uploaded to IPFS', { variant: 'success' });

      // Create NFT metadata
      const metadata: NFTMetadata = {
        name: nftName,
        unitName: generateUnitName(nftName),
        totalSupply: parameters.supply || 1,
        description: parameters.description || `NFT created with uploaded image`,
        url: uploadResult.ipfsUrl!
      };

      const result = await transactionService.createNFT(
        activeAddress!,
        metadata,
        transactionSigner!
      );

      await updateBalance();
      
      if (result.status === 'success') {
        addBotMessage(result.message, 'success', result.txid);
        enqueueSnackbar('NFT created successfully!', { variant: 'success' });
        // Clear pending image after successful creation
        clearPendingImage();
        
        // Auto-opt-in to the new asset
        if (result.txid && result.message.includes('Asset ID:')) {
          const assetIdMatch = result.message.match(/Asset ID: (\d+)/);
          if (assetIdMatch) {
            const assetId = Number(assetIdMatch[1]);
            addBotMessage(`🔄 Opting in to asset ${assetId}...`, 'pending');
            enqueueSnackbar('Opting in to new NFT...', { variant: 'info' });
            const optInResult = await transactionService.optInToAsset(
              activeAddress!,
              assetId,
              transactionSigner!
            );
            await updateBalance();
            if (optInResult.status === 'success') {
              addBotMessage(optInResult.message, 'success', optInResult.txid);
              enqueueSnackbar('Auto-opt-in successful!', { variant: 'success' });
            } else {
              addBotMessage(optInResult.message, 'error');
              enqueueSnackbar('Auto-opt-in failed', { variant: 'error' });
            }
          }
        }
      } else {
        addBotMessage(result.message, 'error');
        enqueueSnackbar('NFT creation failed', { variant: 'error' });
      }
    } catch (error) {
      addBotMessage(`❌ Failed to create NFT: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      enqueueSnackbar('NFT creation failed', { variant: 'error' });
    }
  };

  const handleSendNFT = async (parameters: any) => {
    if (!parameters.asset_id || !parameters.recipient) {
      addBotMessage('❌ Missing asset ID or recipient address for NFT transfer.');
      return;
    }

    addBotMessage(`🔄 Sending NFT ${parameters.asset_id} to ${parameters.recipient}...`, 'pending');

    try {
      const result = await transactionService.sendNFT(
        activeAddress!,
        parameters.asset_id,
        parameters.recipient,
        transactionSigner!
      );

      if (result.status === 'success') {
        addBotMessage(result.message, 'success', result.txid);
        enqueueSnackbar('NFT transferred successfully!', { variant: 'success' });
      } else {
        addBotMessage(result.message, 'error');
        enqueueSnackbar('NFT transfer failed', { variant: 'error' });
      }
    } catch (error) {
      addBotMessage(`❌ Failed to send NFT: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const handleOptIn = async (parameters: any) => {
    if (!parameters.asset_id) {
      addBotMessage('❌ Missing asset ID for opt-in.');
      return;
    }

    addBotMessage(`🔄 Opting in to asset ${parameters.asset_id}...`, 'pending');

    try {
      const result = await transactionService.optInToAsset(
        activeAddress!,
        parameters.asset_id,
        transactionSigner!
      );

      if (result.status === 'success') {
        addBotMessage(result.message, 'success', result.txid);
        enqueueSnackbar('Opt-in successful!', { variant: 'success' });
      } else {
        addBotMessage(result.message, 'error');
        enqueueSnackbar('Opt-in failed', { variant: 'error' });
      }
    } catch (error) {
      addBotMessage(`❌ Failed to opt-in: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const handleOptOut = async (parameters: any) => {
    if (!parameters.asset_id) {
      addBotMessage('❌ Missing asset ID for opt-out.');
      return;
    }

    addBotMessage(`🔄 Opting out of asset ${parameters.asset_id}...`, 'pending');

    try {
      const result = await transactionService.optOutOfAsset(
        activeAddress!,
        parameters.asset_id,
        transactionSigner!
      );

      if (result.status === 'success') {
        addBotMessage(result.message, 'success', result.txid);
        enqueueSnackbar('Opt-out successful!', { variant: 'success' });
      } else {
        addBotMessage(result.message, 'error');
        enqueueSnackbar('Opt-out failed', { variant: 'error' });
      }
    } catch (error) {
      addBotMessage(`❌ Failed to opt-out: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const handleCheckBalance = async () => {
    addBotMessage(`🔄 Checking balance for ${activeAddress}...`, 'pending');
    enqueueSnackbar('Checking balance...', { variant: 'info' });
    try {
      const balance = await transactionService.getAccountBalance(activeAddress!);
      setAccountInfo(balance);
      addBotMessage(`💰 Balance: ${balance.algo.toFixed(6)} ALGO\nAssets: ${balance.assets.length}`, 'success');
      enqueueSnackbar('Balance updated', { variant: 'success' });
    } catch (error) {
      addBotMessage(`❌ Failed to check balance: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      enqueueSnackbar('Failed to check balance', { variant: 'error' });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // After every transaction or balance check, update balance
  const updateBalance = async () => {
    if (activeAddress) {
      try {
        const info = await transactionService.getAccountBalance(activeAddress);
        setAccountInfo(info);
      } catch (error) {
        enqueueSnackbar('Failed to fetch balance', { variant: 'error' });
      }
    }
  };

  // Add a message with the widget
  const addWidgetMessage = (params: { fromAsset?: string; toAsset?: string; amount?: number }) => {
    const newMessage: ChatMessage = {
      id: `${Date.now()}-${messageCounter++}`,
      type: 'widget',
      content: '',
      timestamp: new Date(),
      widgetParams: params,
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  // Update the Tinyman swap handler
  const handleSwapTokens = async (parameters: any) => {
    if (!parameters.from_asset || !parameters.to_asset || !parameters.amount) {
      addBotMessage('❌ Missing required parameters for swap. Please specify from_asset, to_asset, and amount.');
      return;
    }

    if (!activeAddress) {
      addBotMessage('❌ Please connect your wallet first to perform swaps.');
      return;
    }

    // Show confirmation message
    addBotMessage(`🔄 Opening swap widget for ${parameters.amount} ${parameters.from_asset} → ${parameters.to_asset}...`);
    // Add the widget as a chat message
    addWidgetMessage({
      fromAsset: parameters.from_asset,
      toAsset: parameters.to_asset,
      amount: parameters.amount,
    });
  };

  const handleSetLimitOrder = async (parameters: any) => {
    if (!parameters.from_asset || !parameters.to_asset || !parameters.amount || !parameters.trigger_price) {
      addBotMessage('❌ Missing required parameters for limit order. Please specify from_asset, to_asset, amount, and trigger_price.');
      return;
    }

    const orderType = parameters.trade_type === 'buy' ? 'buy' : 'sell';
    addBotMessage(`🔄 Setting limit order: ${orderType.toUpperCase()} ${parameters.amount} ${parameters.from_asset} at $${parameters.trigger_price}...`, 'pending');
    
    try {
      const result = await tradingService.setLimitOrder(
        parameters.from_asset,
        parameters.to_asset,
        parameters.amount,
        parameters.trigger_price,
        orderType,
        transactionSigner!,
        activeAddress!
      );

      if (result.status === 'success') {
        addBotMessage(result.message, 'success', result.txid);
        enqueueSnackbar('Limit order set successfully!', { variant: 'success' });
      } else {
        addBotMessage(result.message, 'error');
        enqueueSnackbar('Limit order failed', { variant: 'error' });
      }
    } catch (error) {
      addBotMessage(`❌ Limit order failed: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      enqueueSnackbar('Limit order failed', { variant: 'error' });
    }
  };

  const handleSetStopLoss = async (parameters: any) => {
    if (!parameters.asset || !parameters.amount || !parameters.trigger_price) {
      addBotMessage('❌ Missing required parameters for stop-loss. Please specify asset, amount, and trigger_price.');
      return;
    }

    addBotMessage(`🔄 Setting stop-loss: Sell ${parameters.amount} ${parameters.asset} when price drops to $${parameters.trigger_price}...`, 'pending');
    
    try {
      const result = await tradingService.setStopLoss(
        parameters.asset,
        parameters.amount,
        parameters.trigger_price,
        transactionSigner!,
        activeAddress!
      );

      if (result.status === 'success') {
        addBotMessage(result.message, 'success', result.txid);
        enqueueSnackbar('Stop-loss set successfully!', { variant: 'success' });
      } else {
        addBotMessage(result.message, 'error');
        enqueueSnackbar('Stop-loss failed', { variant: 'error' });
      }
    } catch (error) {
      addBotMessage(`❌ Stop-loss failed: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      enqueueSnackbar('Stop-loss failed', { variant: 'error' });
    }
  };

  const handleCheckPrices = async (parameters: any) => {
    const assets = parameters.asset ? [parameters.asset] : ['algorand', 'bitcoin', 'ethereum'];
    
    addBotMessage(`🔄 Fetching current prices for ${assets.join(', ')}...`, 'pending');
    
    try {
      const prices = await tradingService.getPrices(assets);
      
      if (prices.length > 0) {
        let priceMessage = '📊 Current Market Prices:\n\n';
        prices.forEach(price => {
          const changeColor = price.change24h >= 0 ? '🟢' : '🔴';
          priceMessage += `${price.symbol}: $${price.price.toFixed(4)} ${changeColor}${price.change24h >= 0 ? '+' : ''}${price.change24h.toFixed(2)}%\n`;
        });
        priceMessage += `\nLast updated: ${new Date().toLocaleTimeString()}`;
        
        addBotMessage(priceMessage, 'success');
        enqueueSnackbar('Prices fetched successfully!', { variant: 'success' });
      } else {
        addBotMessage('❌ Unable to fetch current prices. Please try again later.');
        enqueueSnackbar('Failed to fetch prices', { variant: 'error' });
      }
    } catch (error) {
      addBotMessage(`❌ Failed to fetch prices: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      enqueueSnackbar('Failed to fetch prices', { variant: 'error' });
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ width: '100%', minHeight: '60vh', background: 'transparent', boxShadow: 'none', borderRadius: 0, padding: 0 }}>
      {/* Messages Container */}
      <div className="messages-container" style={{ flex: 1, minHeight: 0, padding: 0, background: 'transparent', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
        {messages.map((message) => (
          message.type === 'widget' ? (
            <div key={message.id} className="message bot" style={{ display: 'flex', flexDirection: 'row', alignItems: 'flex-end', gap: '0.7rem', width: '100%' }}>
              <div className="message-content" style={{ borderRadius: '1.5rem', border: '1.5px solid #e0f7fa', background: '#fff', color: '#1a232b', fontWeight: 500, fontSize: '1.08rem', boxShadow: 'none', padding: '1.1rem 1.4rem', maxWidth: '70%', width: 'fit-content' }}>
                <SwapWidget
                  fromAsset={message.widgetParams?.fromAsset}
                  toAsset={message.widgetParams?.toAsset}
                  amount={message.widgetParams?.amount}
                  onSwapCompleted={(data) => {
                    addBotMessage(`✅ Swap completed successfully! Transaction ID: ${data.txid || 'N/A'}`, 'success', data.txid);
                    enqueueSnackbar('Swap completed successfully!', { variant: 'success' });
                    updateBalance();
                  }}
                  onSwapFailed={(data) => {
                    addBotMessage(`❌ Swap failed: ${data.error || 'Unknown error'}`, 'error');
                    enqueueSnackbar('Swap failed', { variant: 'error' });
                  }}
                />
              </div>
            </div>
          ) : (
            <div
              key={message.id}
              className={`message ${message.type}`}
              style={{ display: 'flex', flexDirection: message.type === 'user' ? 'row-reverse' : 'row', alignItems: 'flex-end', gap: '0.7rem', width: '100%' }}
            >
              {/* Bubble */}
              <div
                className="message-content"
                style={{
                  borderRadius: '1.5rem',
                  background: message.type === 'user' ? '#4ecb6e' : '#fff',
                  color: message.type === 'user' ? '#fff' : '#1a232b',
                  borderBottomRightRadius: message.type === 'user' ? '0.7rem' : '1.5rem',
                  borderBottomLeftRadius: message.type === 'bot' ? '0.7rem' : '1.5rem',
                  border: message.type === 'bot' ? '1.5px solid #e0f7fa' : 'none',
                  fontWeight: 500,
                  fontSize: '1.08rem',
                  boxShadow: 'none',
                  padding: '1.1rem 1.4rem',
                  maxWidth: '70%',
                  marginLeft: message.type === 'user' ? 0 : '0.2rem',
                  marginRight: message.type === 'bot' ? 0 : '0.2rem',
                  marginBottom: 0,
                  width: 'fit-content',
                }}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                
                {/* Display image if present */}
                {message.imageUrl && (
                  <div style={{ marginTop: '0.8rem', borderRadius: '0.8rem', overflow: 'hidden' }}>
                    <img 
                      src={message.imageUrl} 
                      alt="Uploaded content"
                      style={{ 
                        maxWidth: '100%', 
                        maxHeight: '200px', 
                        borderRadius: '0.8rem',
                        objectFit: 'cover'
                      }}
                    />
                  </div>
                )}
                
                {message.status && (
                  <div className={`message-status ${message.status}`} style={{ marginTop: '0.5rem', fontSize: '0.9rem', opacity: 0.8 }}>
                    {message.status === 'pending' && '⏳ Processing...'}
                    {message.status === 'success' && '✅ Success'}
                    {message.status === 'error' && '❌ Failed'}
                  </div>
                )}
                {message.txid && (
                  <div className="message-status" style={{ marginTop: '0.3rem', fontSize: '0.85rem', opacity: 0.7 }}>
                    TxID: {message.txid.substring(0, 8)}...
                  </div>
                )}
              </div>
            </div>
          )
        ))}
        {isProcessing && (
          <div className="message bot" style={{ display: 'flex', flexDirection: 'row', alignItems: 'flex-end', gap: '0.7rem', width: '100%' }}>
            <div className="message-content" style={{ borderRadius: '1.5rem', border: '1.5px solid #e0f7fa', background: '#fff', color: '#1a232b', fontWeight: 500, fontSize: '1.08rem', boxShadow: 'none', padding: '1.1rem 1.4rem', maxWidth: '70%', width: 'fit-content' }}>
              <div className="flex items-center space-x-2">
                <div className="loading-spinner"></div>
                <span>Processing...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {/* Input Area at the very bottom */}
      <div className="input-area" style={{ width: '100%', background: 'transparent', padding: '0.7rem 0 1.2rem 0', position: 'sticky', bottom: 0 }}>
        {/* Pending Image Indicator */}
        {pendingImage && (
          <div style={{ 
            background: '#e8f5e8', 
            border: '1px solid #4ecb6e', 
            borderRadius: '1rem', 
            padding: '0.8rem', 
            marginBottom: '0.8rem', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.8rem',
            maxWidth: 720,
            margin: '0 auto 0.8rem auto'
          }}>
            <div style={{ 
              width: '40px', 
              height: '40px', 
              borderRadius: '0.5rem', 
              overflow: 'hidden', 
              flexShrink: 0 
            }}>
              <img 
                src={pendingImage.preview} 
                alt="Pending image"
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, color: '#1a232b', fontSize: '0.95rem' }}>
                📸 Image Ready for NFT Creation
              </div>
              <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.2rem' }}>
                Type "create NFT" or "create NFT named [name]" to use this image
              </div>
            </div>
            <button
              onClick={clearPendingImage}
              style={{ 
                background: 'none', 
                border: 'none', 
                color: '#666', 
                cursor: 'pointer', 
                padding: '0.3rem',
                borderRadius: '0.3rem',
                fontSize: '1.2rem'
              }}
              title="Remove pending image"
            >
              ✕
            </button>
          </div>
        )}
        
        <div className="input-container" style={{ background: '#fff', borderRadius: '2rem', boxShadow: '0 2px 8px rgba(0,0,0,0.03)', padding: '0.5rem 0.7rem', display: 'flex', alignItems: 'center', gap: '0.7rem', width: '100%', maxWidth: 720, margin: '0 auto' }}>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="file-btn"
            title="Attach file"
            style={{ background: 'none', border: 'none', padding: 0, marginRight: '0.2rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            <svg width="22" height="22" fill="none" stroke="#4ecb6e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M21.44 11.05l-9.19 9.19a5 5 0 01-7.07-7.07l9.19-9.19a3 3 0 014.24 4.24l-9.2 9.19a1 1 0 01-1.41-1.41l9.2-9.19"/></svg>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/*"
            onChange={handleFileSelect}
            className="file-input"
            style={{ display: 'none' }}
          />
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={pendingImage ? "Type 'create NFT' or your message..." : "Type your message here... (e.g., 'send 2 ALGO to K54ZTTHNDB...')"}
            className="text-input"
            disabled={isProcessing}
            style={{ background: 'transparent', border: 'none', outline: 'none', fontSize: '1.08rem', flex: 1 }}
          />
          <button
            onClick={handleSendMessage}
            disabled={isProcessing || (!inputMessage.trim() && !selectedFile)}
            className="send-btn"
            style={{ background: '#4ecb6e', color: '#fff', border: 'none', borderRadius: '1.5rem', fontWeight: 700, fontSize: '1.08rem', padding: '0.9rem 1.5rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
          >
            <svg width="22" height="22" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>
          </button>
        </div>
        {!activeAddress && (
          <div className="mt-2 text-sm text-red-600" style={{ textAlign: 'center' }}>
            ⚠️ Please connect your wallet to use Algo-Intent
          </div>
        )}
      </div>
    </div>
  );
};

export default AlgoIntentChat; 