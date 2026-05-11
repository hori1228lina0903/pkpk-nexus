class CardSearchApp {
    constructor() {
        this.dataLoader = new DataLoader();
        // 即時にCardSearchを初期化してスケルトン表示
        this.cardSearch = new CardSearch([]);
        this.cardSearch.showLoadingSkeleton();
        this.init();
    }
    
    async init() {
        try {
            // まず全ての画像の読み込みを待つ
            await this.waitForPageImages();
            
            console.log('🔍 カードデータの読み込みを開始...');
            const cardData = await this.dataLoader.loadCards();
            
            if (!cardData || cardData.length === 0) {
                console.warn('⚠️ カードデータが空です');
                this.cardSearch.showError('カードデータが見つかりませんでした');
                return;
            }
            
            // ファイル構造をデバッグ
            console.log('📁 ファイル構造デバッグ:');
            console.log('  - 読み込んだカード数:', cardData.length);
            cardData.forEach((card, i) => {
                console.log(`  ${i+1}. ${card['名前']} - 番号: ${JSON.stringify(card['カード番号'])}`);
            });
            
            // カード画像を事前読み込み（デバッグ版）
            await this.preloadCardImages(cardData);
            
            // データ到着後にCardSearchを更新
            this.cardSearch.updateCardData(cardData);
            
            // ★★★ showAllCards() の代わりに空検索を実行 ★★★
            // これでフィルターがクリアされた状態で無限スクロールが初期化される
            this.cardSearch.performSearch();
            
            // リセットボタンの設定
            this.setupResetButton();
            
        } catch (error) {
            console.error('❌ カードデータの読み込みに失敗:', error);
            console.error('エラー詳細:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            this.cardSearch.showError('カードデータの読み込みに失敗しました: ' + error.message);
        }
    }
    
    // ページ内の全ての画像を待つ
    waitForPageImages() {
        return new Promise((resolve) => {
            const images = document.querySelectorAll('img');
            let loadedCount = 0;
            
            if (images.length === 0) {
                resolve();
                return;
            }
            
            images.forEach(img => {
                if (img.complete) {
                    loadedCount++;
                } else {
                    img.addEventListener('load', () => {
                        loadedCount++;
                        if (loadedCount === images.length) resolve();
                    });
                    img.addEventListener('error', () => {
                        loadedCount++;
                        if (loadedCount === images.length) resolve();
                    });
                }
            });
            
            if (loadedCount === images.length) resolve();
        });
    }
    
    // カード画像を事前読み込み
async preloadCardImages(cardData) {
    console.log(`🔄 ${cardData.length}枚のカード画像を事前読み込み中...`);
    
    // 最初の6枚だけ先行読み込み
    const previewCards = cardData.slice(0, 6);
    
    // Promise.all を使わず、並列実行
    previewCards.forEach((card, index) => {
        const img = new Image();
        const imagePath = this.cardSearch.getCardImagePath(card);
        
        // 低優先度でバックグラウンド読み込み
        setTimeout(() => {
            img.src = imagePath;
        }, index * 50);
    });
    
    console.log('✅ 事前読み込み開始');
    // 完了を待たずに続行
    return Promise.resolve();
}
    
    setupResetButton() {
        const resetButton = document.getElementById('resetSearch');
        if (resetButton) {
            resetButton.addEventListener('click', () => {
                // 検索ボックスだけクリア
                document.getElementById('cardSearch').value = '';
                
                // ★★★ showAllCards() ではなく、performSearch() を呼び出す ★★★
                // これで現在のフィルター状態が保持されたまま検索が実行される
                this.cardSearch.performSearch();
            });
        }
    }
}

// DOM読み込み完了後にクラス追加
document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('loaded');
    new CardSearchApp();
});