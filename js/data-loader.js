class DataLoader {
    constructor() {
        this.cardData = [];
        this.isLoaded = false;
    }

    async loadCards() {
        if (this.isLoaded) return this.cardData;

        try {
            console.log('🚀 データ読み込み開始...');
            
            // 【運用】読み込むファイルの一覧
            const packs = [
                'a1-all-cards.json',
                'a1a-all-cards.json',
                'a2-all-cards.json',
                'a2a-all-cards.json',
                'a2b-all-cards.json',
                'a3-all-cards.json',
                'a3a-all-cards.json',
                'a3b-all-cards.json',
                'a4-all-cards.json',
                'a4a-all-cards.json',
                'a4b-all-cards.json',
                'b1-all-cards.json',
                'b1a-all-cards.json',
                'b2-all-cards.json',
                'b2a-all-cards.json',
                'b2b-all-cards.json',
                'b3-all-cards.json',
                'promo-a-all-cards.json',
                'promo-b-all-cards.json'
            ];

            const loadPromises = packs.map(async (fileName) => {
                const response = await fetch(`/data/cards/${fileName}`); 
                if (!response.ok) {
                    console.warn(`⚠️ ファイルが見つかりません: ${fileName}`);
                    return [];
                }
                
                const data = await response.json();
                
                // ★ キー判定ロジック
                let autoKey = fileName.split('-')[0]; // 通常は a1, b1 等

                // ファイル名に "promo" が含まれていたら、一律 "Promo" に書き換える
                // これにより pack_set_name.json の "Promo" キーと一致する
                if (fileName.toLowerCase().includes('promo')) {
                    autoKey = "Promo";
                }

                console.log(`📦 ロード: ${fileName} -> 検索キー: ${autoKey}`);

                return data.map(card => {
                    // 各カードに検索用のキーを付与
                    card._packKey = autoKey; 

                    // 入手方法のテキスト化
                    if (card['入手方法'] && Array.isArray(card['入手方法'])) {
                        card._allSources = card['入手方法'].join(' ');
                    } else {
                        card._allSources = "";
                    }
                    
                    return card;
                });
            });

            const results = await Promise.all(loadPromises);
            
            this.cardData = results.flat();
            this.isLoaded = true;

            console.log(`✅ 合計 ${this.cardData.length} 枚を読み込みました`);
            return this.cardData;

        } catch (error) {
            console.error('❌ 読み込みエラー:', error);
            return [];
        }
    }

    getCardByName(name) {
        return this.cardData.find(card => card['名前'] === name);
    }
}

window.DataLoader = DataLoader;
