export interface IPFSUploadResult {
  success: boolean;
  ipfsHash?: string;
  ipfsUrl?: string;
  error?: string;
}

export class IPFSService {
  private apiKey: string;
  private apiSecret: string;
  private endpoint: string;

  constructor() {
    this.apiKey = import.meta.env.VITE_PINATA_API_KEY || '';
    this.apiSecret = import.meta.env.VITE_PINATA_API_SECRET || '';
    this.endpoint = 'https://api.pinata.cloud/pinning/pinFileToIPFS';
  }

  async uploadToIPFS(file: File): Promise<IPFSUploadResult> {
    if (!this.apiKey || !this.apiSecret) {
      return {
        success: false,
        error: 'Missing Pinata credentials. Please set VITE_PINATA_API_KEY and VITE_PINATA_API_SECRET in your environment variables.'
      };
    }

    try {
      // Validate file size (1GB = 1024MB)
      const fileSizeMB = file.size / (1024 * 1024);
      if (fileSizeMB > 1024) {
        return {
          success: false,
          error: `File too large (${fileSizeMB.toFixed(2)}MB). Max size: 1GB`
        };
      }

      console.log(`Uploading ${file.name} (${fileSizeMB.toFixed(2)}MB) to IPFS...`);

      const formData = new FormData();
      formData.append('file', file);

      // Extended timeout for larger files (10 minutes)
      const timeout = fileSizeMB > 50 ? 600000 : 120000;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'pinata_api_key': this.apiKey,
          'pinata_secret_api_key': this.apiSecret,
        },
        body: formData,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Pinata upload failed: HTTP ${response.status} - ${response.statusText}`);
      }

      const result = await response.json();
      
      if (!result.IpfsHash) {
        throw new Error('Pinata response missing IPFS hash');
      }

      console.log(`Successfully uploaded to IPFS: ${result.IpfsHash}`);
      
      return {
        success: true,
        ipfsHash: result.IpfsHash,
        ipfsUrl: `ipfs://${result.IpfsHash}`
      };

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        const fileSizeMB = file.size / (1024 * 1024);
        const timeout = fileSizeMB > 50 ? 600000 : 120000;
        return {
          success: false,
          error: `Upload timed out after ${timeout / 60000} minutes`
        };
      }

      return {
        success: false,
        error: `Failed to upload ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  async uploadFromDataURL(dataURL: string, filename: string): Promise<IPFSUploadResult> {
    try {
      // Convert data URL to blob
      const response = await fetch(dataURL);
      const blob = await response.blob();
      
      // Create file from blob
      const file = new File([blob], filename, { type: blob.type });
      
      return await this.uploadToIPFS(file);
    } catch (error) {
      return {
        success: false,
        error: `Failed to process image: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }
}

export const ipfsService = new IPFSService(); 