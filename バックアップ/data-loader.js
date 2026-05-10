class DataLoader {
    constructor() {
        this.cardData = [];
    }

    async loadCards() {
        try {
            console.log('カードデータを読み込み中...');
            
            // インデックスファイルを読み込み
            const indexResponse = await fetch('/cards/index.json');
            if (!indexResponse.ok) {
                console.error('❌ index.jsonの読み込みに失敗');
                return [];
            }
            
            const filePaths = await indexResponse.json();
            console.log('📁 index.jsonの内容:', filePaths);
            console.log(`📁 ${filePaths.length}個のカードファイルを検出`);
            
            // すべてのカードファイルを読み込み
            const cardPromises = filePaths.map(filePath =>
                this.loadSingleCard(`/cards/${filePath}`)
            );
            
            const allCards = await Promise.all(cardPromises);
            
            // nullを除去して結合
            this.cardData = allCards.filter(card => card !== null);
            
            console.log(`✅ ${this.cardData.length}枚のカードを読み込みました`);
            return this.cardData;
            
        } catch (error) {
            console.error('❌ カードデータの読み込みエラー:', error);
            // エラー時は空配列を返す
            return [];
        }
    }

async loadSingleCard(fullPath) {
    try {
        const response = await fetch(fullPath);
        if (!response.ok) return null;
        
        const cardData = await response.json();
        
        // ファイルパスからパックキーを抽出
        const pathParts = fullPath.split('/');
        if (pathParts.length >= 3) {
            let packKey = pathParts[2]; // /cards/[packKey]/.../filename.json
            
            // "promo-a" を "Promo" に正規化
            if (packKey.toLowerCase().startsWith('promo')) {
                packKey = 'Promo';
            }
            
            cardData._packKey = packKey;
        }
        
        return cardData;
        
    } catch (error) {
        console.warn(`${fullPath} の読み込みに失敗:`, error);
        return null;
    }
}

    // ファイルアクセステストメソッドを追加
    async testFileAccess() {
        console.log('🔧 ファイルアクセステスト開始');
        
        const testPaths = [
            '/cards/index.json',
            '/cards/a1/1/Bulbasaur.json',
            '/cards/a1/2/Ivysaur.json',
            '/cards/a1/3/Venusaur.json'
        ];
        
        for (const path of testPaths) {
            try {
                const response = await fetch(path);
                console.log(`📁 ${path}: ${response.status} ${response.ok ? '✅' : '❌'}`);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log(`   📄 内容: ${data['名前'] || 'index file'}`);
                }
            } catch (error) {
                console.error(`📁 ${path}: ❌ ${error.message}`);
            }
        }
    }

    getAllCards() {
        return this.cardData;
    }
}

window.DataLoader = DataLoader;