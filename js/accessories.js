// 実際の画像が置かれているベースパス
const IMAGE_BASE_PATH = '/images/accessories';

// JSONのパスを実際の画像パスに変換する関数
function getActualImagePath(jsonPath) {
    return `${IMAGE_BASE_PATH}/${jsonPath}`;
}

// ファイル名からカテゴリ接尾辞を除去する関数
function formatDisplayName(fileName) {
    // 除去する接尾辞のリスト
    const suffixes = [
        '_backdrop',
        '_card_sleeve',
        '_playmat',
        '_cover',
        '_icon',
        '_Pokémon_coin',
    ];
    
    let displayName = fileName;
    
    // 接尾辞を除去
    suffixes.forEach(suffix => {
        if (displayName.endsWith(suffix)) {
            displayName = displayName.slice(0, -suffix.length);
        }
    });
    
    // アンダースコアをスペースに変換
    displayName = displayName.replace(/_/g, ' ');
    
    return displayName;
}

// 画像データを取得して表示する関数
async function loadAccessories() {
    try {
        // 新しいJSONファイルを取得
        const response = await fetch('/data/accessories_by_release_new.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // カテゴリごとに画像を設定（JSONの構造に合わせて修正）
        const categories = {
            'icon': data.icons || [],
            'playmat': data.playmats || [],
            'cardsleeve': data.card_sleeves || [],
            'coin': data.coins || [],
            'cover': data.covers || [],
            'backdrop': data.backdrops || []
        };
        
        // 各カテゴリのグリッドに画像を表示
        for (const [category, items] of Object.entries(categories)) {
            const gridElement = document.getElementById(`${category}-grid`);
            if (!gridElement) continue;
            
            if (items.length === 0) {
                gridElement.innerHTML = '<div class="error">No images found</div>';
                continue;
            }
            
            // グリッドのHTMLを生成
            let html = '';
            items.forEach((imagePath, index) => {
                // 番号（1から開始）
                const number = index + 1;
                
                // ファイル名から拡張子を除去
                const fileName = imagePath.split('/').pop().replace(/\.webp$/, '');
                // 表示用にフォーマット
                const displayName = formatDisplayName(fileName);
                // 実際の画像パスを取得
                const actualPath = getActualImagePath(imagePath);
                
                html += `
                    <div class="accessory-item">
                        <img src="${actualPath}" alt="${displayName}" loading="lazy">
                        <div class="accessory-name">${number}. ${displayName}</div>
                    </div>
                `;
            });
            
            gridElement.innerHTML = html;
        }
        
    } catch (error) {
        console.error('Error loading accessories:', error);
        const grids = ['icon', 'playmat', 'cardsleeve', 'coin', 'cover', 'backdrop'];
        grids.forEach(gridId => {
            const element = document.getElementById(`${gridId}-grid`);
            if (element) {
                element.innerHTML = `<div class="error">Failed to load images: ${error.message}</div>`;
            }
        });
    }
}

// カテゴリタブ切り替え機能
function setupTabs() {
    const tabs = document.querySelectorAll('.accessory-tab');
    const contents = document.querySelectorAll('.accessory-category-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const category = tab.dataset.category;
            
            // タブのアクティブ状態を更新
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // コンテンツの表示/非表示を切り替え
            contents.forEach(content => {
                if (content.id === `${category}-content`) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
        });
    });
}

// ページ読み込み時に実行（既存の行を置き換え）
document.addEventListener('DOMContentLoaded', () => {
    loadAccessories();
    setupTabs();
});