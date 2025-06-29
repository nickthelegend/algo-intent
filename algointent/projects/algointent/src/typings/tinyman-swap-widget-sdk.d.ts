declare module '@tinymanorg/tinyman-swap-widget-sdk' {
  export class WidgetController {
    constructor(options: any);
    static generateWidgetIframeUrl(options: any): string;
    static sendMessageToWidget(args: any): void;
    addWidgetEventListeners(): void;
    removeWidgetEventListeners(): void;
  }
} 