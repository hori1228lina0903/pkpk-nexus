class CardSearch {
constructor(cardData) {
    this.cardData = cardData || [];
    this.currentFilters = {
        type: [],
        cardType: [],
        rarity: [],
        hpMin: null,
        hpMax: null,
        other: [],
        trainer: [],
        damageMin: null,
        damageMax: null,
        pack: []
    };
    
    console.log('🔄 CardSearchコンストラクター: フィルター初期化完了');
    
    // ★★★ 無限スクロール用のプロパティを追加 ★★★
    this.isLoadingMore = false;
    this.hasMoreCards = false;
    this.displayedCards = 0;
    this.batchSize = 24;
    this.currentSearchResults = [];
    this.scrollTimer = null;
    
    // メソッドをバインド
    this.setupAdvancedFiltersToggle = this.setupAdvancedFiltersToggle.bind(this);
    this.restoreFilterState = this.restoreFilterState.bind(this);
    
    // 基本的なセットアップ
    this.setupSearch();
    this.setupFilterButtons();
    this.setupResetButton();
    this.setupHpFilter();
    this.setupDamageFilter();
    this.setupAdvancedFiltersToggle();  
    this.restoreFilterState();
    this.activateAllCardTypeButton();
    this.setupPackResetButton();
    this.setupAdvancedFiltersResetButton();
    
    this.searchTimer = null;
    this.debounceDelay = 400;
    this.currentSearchId = 0;
    
    this.imageCache = new Map();
    this.failedImages = new Set();
    
    // ★★★ パックフィルターを初期化 ★★★
    this.setupPackFilter();
    
    // パック選択の状態を確実に初期化
    setTimeout(() => {
        this.initializePackSelectState();
    }, 100);
    
    // ★★★ 無限スクロールを初期化（遅延読み込みもセットアップ） ★★★
    setTimeout(() => {
        this.setupInfiniteScroll();
        this.setupLazyLoading(); // ★★★ 遅延画像読み込みをセットアップ ★★★
    }, 1000);
    
    // カード表示 - 修正版
    if (this.cardData && this.cardData.length > 0) {
        setTimeout(() => {
            const searchId = ++this.currentSearchId;
            this.handleSearch('', searchId);
        }, 200);
    } else {
        this.showLoadingSkeleton();
    }
}

// 1. 無限スクロールセットアップ
setupInfiniteScroll() {
    const resultsContainer = document.getElementById('resultsContainer');
    if (!resultsContainer) {
        console.warn('⚠️ 結果コンテナが見つかりません');
        return;
    }
    
    console.log('✅ 結果コンテナを取得:', resultsContainer);
    
    // スクロールイベントのリスナーを追加
    resultsContainer.addEventListener('scroll', () => {
        this.handleScroll();
    });
    
    console.log('✅ スクロールイベントリスナーを追加');
    
    // タッチデバイス用のリサイズイベントも考慮
    window.addEventListener('resize', () => {
        this.checkIfNeedMoreCards();
    });
    
    console.log('✅ リサイズイベントリスナーを追加');
    
    // 初期ロード後にもカードが必要かチェック
    setTimeout(() => {
        this.checkIfNeedMoreCards();
    }, 500);
    
    console.log('✅ 無限スクロールセットアップ完了');
}

// 2. スクロールハンドラー
handleScroll() {
    // リクエストアニメーションフレームを使用
    if (this.scrollAnimationFrame) {
        cancelAnimationFrame(this.scrollAnimationFrame);
    }
    
    this.scrollAnimationFrame = requestAnimationFrame(() => {
        if (this.isLoadingMore || !this.hasMoreCards) {
            return;
        }
        
        const resultsContainer = document.getElementById('resultsContainer');
        if (!resultsContainer) return;
        
        // 軽量な計算
        const scrollBottom = resultsContainer.scrollHeight - 
                           resultsContainer.scrollTop - 
                           resultsContainer.clientHeight;
        
        if (scrollBottom < 500) { // 閾値を少し広く
            this.loadMoreCards();
        }
    });
}

// 3. 追加カードが必要かチェック
checkIfNeedMoreCards() {
    
    const resultsContainer = document.getElementById('resultsContainer');
    if (!resultsContainer) {
        console.warn('⚠️ 結果コンテナが見つかりません');
        return;
    }
    
    // ロード中または追加カードがない場合はスキップ
    if (this.isLoadingMore || !this.hasMoreCards) {
        return;
    }
    
    // 現在の表示状態を取得
    const currentScrollHeight = resultsContainer.scrollHeight;
    const currentClientHeight = resultsContainer.clientHeight;
    
    // ★★★ 条件を緩和: コンテナの高さがスクロール高さより大きい場合もロード ★★★
    if (currentScrollHeight <= currentClientHeight * 1.5) {
        this.loadMoreCards();
    } else {
    }
}

// 4. 追加カードをロード
async loadMoreCards() {
    
    if (this.isLoadingMore || !this.hasMoreCards) {
        return;
    }
    
    this.isLoadingMore = true;
    
    const startIndex = this.displayedCards;
    const endIndex = Math.min(startIndex + this.batchSize, this.currentSearchResults.length);
    
    // 表示するカードが残っていない場合
    if (startIndex >= this.currentSearchResults.length) {
        this.hasMoreCards = false;
        this.isLoadingMore = false;
        return;
    }
    
    // ローディングインジケーターを表示
    this.showLoadingIndicator();
    
    try {
        // バッチのカードを取得
        const batchCards = this.currentSearchResults.slice(startIndex, endIndex);
        
        // カードHTMLを生成
        const cardsHTML = await this.generateCardsHTML(batchCards);
        
        // 結果コンテナに追加
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
            // ローディングインジケーターを削除
            const loadingIndicator = resultsContainer.querySelector('.loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
            
            // カードを追加
            resultsContainer.insertAdjacentHTML('beforeend', cardsHTML);
            
            // 表示カード数を更新
            this.displayedCards = endIndex;
            
            // さらにカードがあるかチェック
            this.hasMoreCards = this.displayedCards < this.currentSearchResults.length;
            
            // ★★★ 重要: 遅延読み込みを再初期化 ★★★
            setTimeout(() => {
                if (this.observeImagesAfterLoad) {
                    this.observeImagesAfterLoad();
                }
            }, 50);
            
            // カードがまだある場合は、さらに必要かチェック
            if (this.hasMoreCards) {
                setTimeout(() => this.checkIfNeedMoreCards(), 100);
            }
        }
    } catch (error) {
        console.error('❌ カードロードエラー:', error);
    } finally {
        this.isLoadingMore = false;
    }
}

// 5. 最初のバッチのカードを表示
async showFirstBatchOfResults(results) {
    const resultsContainer = document.getElementById('resultsContainer');
    if (!resultsContainer) return;
    
    // 結果コンテナをクリア
    resultsContainer.innerHTML = '';
    
    // 検索結果数を表示（即時）
    this.updateResultsCount(results.length, this.cardData.length);
    
    if (results.length === 0) {
        resultsContainer.style.display = 'grid';
        resultsContainer.innerHTML = `
            <div class="no-results">
                <p>該当するカードが見つかりませんでした</p>
            </div>
        `;
        return;
    }
    
    // 最初のバッチ（最大24枚）を取得
    const firstBatch = results.slice(0, this.batchSize);
    this.displayedCards = firstBatch.length;
    this.hasMoreCards = results.length > this.batchSize;
    
    // ★★★ 同期的にHTML生成（async/await を外す）★★★
    const cardsHTML = this.generateCardsHTML(firstBatch);
    
    // 結果を表示
    resultsContainer.style.display = 'grid';
    resultsContainer.innerHTML = cardsHTML;
    
    // ★★★ 画像の遅延読み込みを開始 ★★★
    setTimeout(() => {
        this.startImageLoading();
    }, 0);
    
    // さらにカードが必要かチェック
    if (this.hasMoreCards) {
        setTimeout(() => this.checkIfNeedMoreCards(), 100);
    }
}

// 新しいメソッド：画像読み込みを開始
startImageLoading() {
    const container = document.getElementById('resultsContainer');
    if (!container) return;
    
    const images = container.querySelectorAll('img[data-src]');
    
    // 最初の8枚を即時読み込み
    const immediateLoad = Math.min(8, images.length);
    
    for (let i = 0; i < immediateLoad; i++) {
        const img = images[i];
        if (img.dataset.src) {
            img.src = img.dataset.src;
            img.classList.remove('lazy', 'lazy-load');
            delete img.dataset.src;
        }
    }
    
    // 残りはIntersectionObserverで遅延読み込み
    if (images.length > immediateLoad) {
        this.setupLazyLoadingForRemaining(images, immediateLoad);
    }
}

// 6. カードHTML生成メソッド（新規）
generateCardsHTML(cards) {
    const cardsHTML = [];
    const now = Date.now();
    
    const shouldPreload = this.displayedCards === 0;
    const preloadCount = shouldPreload ? Math.min(16, cards.length) : 0;
    
    for (let i = 0; i < cards.length; i++) {
        const card = cards[i];
        const imagePath = this.getCardImagePath(card);
        const cardName = card['名前'] || 'Unknown';
        const cacheBuster = `?t=${now}`;
        
        // --- リンク生成ロジック ---
        let cardLink = "#";
        
        // 「カード番号」は配列なので、最初の要素 [0] を取得する
        const cardNumberData = card['カード番号'];
        let rawNumber = "";
        
        if (Array.isArray(cardNumberData) && cardNumberData.length > 0) {
            rawNumber = cardNumberData[0]; // "a1#1" を取得
        } else if (typeof cardNumberData === 'string') {
            rawNumber = cardNumberData;
        }

        if (rawNumber && rawNumber.includes('#')) {
            const parts = rawNumber.split('#');
            const packFolder = parts[0]; // a1
            const numberPart = parts[1]; // 1
            
            // 名前のスペースを "_" に置換
            const sanitizedName = cardName.replace(/\s+/g, '_');
            
            // 形式: /cards/a1/1/Bulbasaur.html
            cardLink = `/cards/${packFolder}/${numberPart}/${sanitizedName}.html`;
        }

        // --- HTML生成 ---
        if (i < preloadCount) {
            cardsHTML.push(`
                <a href="${cardLink}" class="card" data-card-name="${cardName}">
                    <div class="card-image">
                        <img src="${imagePath}${cacheBuster}" alt="${cardName}" 
                             class="card-img" loading="eager" data-index="${this.displayedCards + i}">
                    </div>
                </a>
            `);
        } else {
            cardsHTML.push(`
                <a href="${cardLink}" class="card" data-card-name="${cardName}">
                    <div class="card-image">
                        <img src="/images/cards/placeholder.webp" alt="${cardName}"
                             data-src="${imagePath}${cacheBuster}" 
                             class="card-img lazy" loading="lazy" data-index="${this.displayedCards + i}">
                        <div class="image-loading"></div>
                    </div>
                </a>
            `);
        }
    }
    
    return cardsHTML.join('');
}





// 7. ローディングインジケーター表示
showLoadingIndicator() {
    const resultsContainer = document.getElementById('resultsContainer');
    if (!resultsContainer) return;
    
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = `
        <div class="spinner"></div>
        <p>Loading more cards...</p>
    `;
    
    resultsContainer.appendChild(loadingIndicator);
}

setupLazyLoading() {
    
    let observer = null;
    
    // IntersectionObserver が利用可能かチェック
    if ('IntersectionObserver' in window) {
        observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.dataset.src;
                    
                    if (src && img.src !== src) {
                        img.src = src;
                        img.classList.remove('lazy');
                        img.classList.add('loaded');
                        img.onload = () => {
                        };
                    }
                    
                    observer.unobserve(img);
                }
            });
        }, {
            // ★★★ ここを修正 ★★★
            // root: document.getElementById('resultsContainer'), ← これを削除！
            rootMargin: '200px 0px',
            threshold: 0.1
        });
    }
    
    // 遅延画像を監視する関数
    const observeLazyImages = () => {
        const lazyImages = document.querySelectorAll('img.lazy:not(.observed)');
        
        lazyImages.forEach(img => {
            img.classList.add('observed');
            
            if (observer) {
                observer.observe(img);
            } else {
                // IntersectionObserverが使えない場合のフォールバック
                const src = img.dataset.src;
                if (src) {
                    setTimeout(() => {
                        img.src = src;
                        img.classList.remove('lazy');
                        img.classList.add('loaded');
                    }, 100);
                }
            }
        });
    };
    
    const container = document.getElementById('resultsContainer');
    if (container) {
        // スクロールイベントリスナー
        const scrollHandler = () => {
            observeLazyImages();
        };
        
        container.addEventListener('scroll', scrollHandler, { passive: true });
        container.addEventListener('wheel', scrollHandler, { passive: true });
        container.addEventListener('touchmove', scrollHandler, { passive: true });
        
        // 初期チェック
        setTimeout(observeLazyImages, 100);
        
        // カード追加後にもチェック
        this.observeImagesAfterLoad = observeLazyImages;
        
    }
}

setupLazyLoadingForRemaining(images, startIndex) {
    if (!('IntersectionObserver' in window)) {
        // フォールバック：残りを一括読み込み
        for (let i = startIndex; i < images.length; i++) {
            const img = images[i];
            setTimeout(() => {
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    delete img.dataset.src;
                }
            }, (i - startIndex) * 50);
        }
        return;
    }
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.classList.remove('lazy', 'lazy-load');
                    delete img.dataset.src;
                }
                observer.unobserve(img);
            }
        });
    }, {
        rootMargin: '200px 0px',
        threshold: 0.01
    });
    
    for (let i = startIndex; i < images.length; i++) {
        observer.observe(images[i]);
    }
}

initializePackSelectState() {
    // 1回だけ実行
    setTimeout(() => {
        this.checkAndFixPackSelectState();
    }, 100);
}
    
    // 状態を確認して修正するメソッド
// checkAndFixPackSelectState メソッドも修正
checkAndFixPackSelectState() {
    const selectSelected = document.querySelector('.pack-selection-group .select-selected');
    const selectItems = document.querySelector('.pack-selection-group .select-items');
    
    if (!selectSelected || !selectItems) return;
    
    // 強制的に閉じた状態にする
    selectItems.style.display = 'none';
    selectItems.style.opacity = '0';
    selectItems.style.transform = 'translateY(-10px)';
    selectSelected.classList.remove('select-arrow-active');
}
    
// 拡張パックリセットボタンの設定
setupPackResetButton() {
    const resetPackButton = document.getElementById('resetPackFilter');
    if (resetPackButton) {
        resetPackButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.resetPackFilter();
        });
    }
}

// 詳細フィルターリセットボタンの設定
setupAdvancedFiltersResetButton() {
    const resetAdvancedButton = document.getElementById('resetAdvancedFilters');
    if (resetAdvancedButton) {
        resetAdvancedButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.resetAdvancedFilters();
        });
    }
}

updateSelectedPacksDisplay() {
    const selectSelected = document.querySelector('.pack-selection-group .select-selected');
    if (!selectSelected) return;

    // 既存の表示をクリア
    selectSelected.innerHTML = '';

    if (this.currentFilters.pack.length === 0) {
        // 何も選択されていない場合は「すべての拡張パック」を表示
        selectSelected.innerHTML = `
            <span>All Expansion Sets</span>
            <div class="select-arrow">▼</div>
        `;
    } else if (this.currentFilters.pack.length === 1) {
        // 選択されたパックが1つの場合
        const packValue = this.currentFilters.pack[0];
        const packOption = document.querySelector(`.select-item[data-value="${packValue}"]`);
        if (packOption) {
            const spanElement = packOption.querySelector('span');
            let text = spanElement ? spanElement.textContent : packValue;
            text = text.trim();
            
            selectSelected.innerHTML = `
                <span>${text}</span>
                <div class="select-arrow">▼</div>
            `;
        } else {
            selectSelected.innerHTML = `
                <span>${packValue}</span>
                <div class="select-arrow">▼</div>
            `;
        }
    } else {
        // 複数選択されている場合
        const count = this.currentFilters.pack.length;
        selectSelected.innerHTML = `
            <span>${count} packs selected</span>
            <div class="select-arrow">▼</div>
        `;
    }
    
    const spanElement = selectSelected.querySelector('span');
    if (spanElement) {
        spanElement.style.fontWeight = 'normal';
    }
}

// パックキー付きの表示テキストを生成
getDisplayTextWithPackKey(selected) {
    // パックキーの場合
    if (this.packData && this.packData[selected]) {
        const displayName = this.packData[selected].set || selected;
        return `${displayName} (${selected})`; // 例: "Genetic Apex (a1)"
    }
    // パック名の場合
    return selected; // 例: "Charizard Pack"
}
    
    // すべてボタンをアクティブにするメソッドを追加
    activateAllCardTypeButton() {
        const allCardTypeButton = document.querySelector('.filter-btn[data-type="cardType"][data-value="all"]');
        if (allCardTypeButton && !allCardTypeButton.classList.contains('active')) {
            allCardTypeButton.classList.add('active');
        }
    }
    
showLoadingSkeleton(count = 12) {
    const resultsContainer = document.getElementById('resultsContainer');
    const staticCards = document.getElementById('staticCards');
    
    if (staticCards) staticCards.style.display = 'none';
    if (resultsContainer) resultsContainer.style.display = 'grid';
    
    if (!resultsContainer) return;
    
    // すでに読み込み中かチェック
    const currentContent = resultsContainer.innerHTML;
    if (currentContent.includes('card-skeleton') || 
        currentContent.includes('loading-indicator')) {
        return;
    }
    
    resultsContainer.innerHTML = Array(count).fill(`
        <div class="card">
            <div class="card-image card-skeleton"></div>
        </div>
    `).join('');
}
    
    // データ更新メソッドを追加
    updateCardData(cardData) {
        this.cardData = cardData || [];
    }
    
    setupSearch() {
        const searchInput = document.getElementById('cardSearch');
        const searchButton = document.getElementById('searchButton');
        
        if (searchButton) {
            searchButton.addEventListener('click', (e) => {
                e.preventDefault(); // フォームの送信を防止
                this.performSearch();
            });
        }
        
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault(); // フォームの送信を防止
                    this.performSearch();
                }
            });
            
            // リアルタイム検索もオプションとして追加（必要に応じて）
            searchInput.addEventListener('input', () => {
                this.performFilteredSearch();
            });
        }
}
    
    setupResetButton() {
        const resetButton = document.getElementById('resetSearch');
        if (resetButton) {
            resetButton.addEventListener('click', () => {
                this.resetSearch();
            });
        }
    }
    
    setupFilterButtons() {
        const filterButtons = document.querySelectorAll('.filter-btn');
        
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // 画像がクリックされた場合の処理
                let targetButton;
                if (e.target.tagName === 'IMG' || 
                    e.target.classList.contains('type-icon') || 
                    e.target.classList.contains('rarity-icon') || 
                    e.target.classList.contains('rarity-icon2') || 
                    e.target.classList.contains('rarity-icon3')) {
                    targetButton = e.target.closest('.filter-btn');
                } else {
                    targetButton = e.target;
                }
                
                if (!targetButton || !targetButton.classList.contains('filter-btn')) {
                    return;
                }
                
                const filterType = targetButton.dataset.type;
                const filterValue = targetButton.dataset.value;
                
                this.toggleFilterButton(targetButton, filterType, filterValue);
                this.performFilteredSearch();
            });
        });
    }
    
    // HPフィルターのセットアップを追加
setupHpFilter() {
    this.generateHpOptions();
    
    const hpMinSelect = document.getElementById('hpMin');
    const hpMaxSelect = document.getElementById('hpMax');
    
    if (hpMinSelect) {
        hpMinSelect.addEventListener('change', () => {
            this.syncHpOptions();
            this.applyHpFilter(); // この行を追加！！！
        });
    }
    
    if (hpMaxSelect) {
        hpMaxSelect.addEventListener('change', () => {
            this.syncHpOptions();
            this.applyHpFilter(); // この行を追加！！！
        });
    }
    
    // 初期状態の同期
    this.syncHpOptions();
}
    
    // HPオプションを動的に生成
generateHpOptions() {
    const hpOptions = this.getHpOptions();
    const hpMinSelect = document.getElementById('hpMin');
    const hpMaxSelect = document.getElementById('hpMax');
    
    if (!hpMinSelect || !hpMaxSelect) return;
    
    // 最小値用のオプションを生成
    hpMinSelect.innerHTML = '<option value="">No min</option>';
    hpOptions.forEach(hp => {
        hpMinSelect.innerHTML += `<option value="${hp}">${hp}</option>`;
    });
    
    // 最大値用のオプションを生成
    hpMaxSelect.innerHTML = '<option value="">No max</option>';
    hpOptions.forEach(hp => {
        hpMaxSelect.innerHTML += `<option value="${hp}">${hp}</option>`;
    });
    // 最大値用に500を追加
    hpMaxSelect.innerHTML += '<option value="500">500</option>';
}
    
    // HPオプションの値を定義（必要に応じて調整可能）
    getHpOptions() {
        return [
            0, 10, 20, 30, 40, 50, 60, 70, 80, 90,
            100, 110, 120, 130, 140, 150, 160, 170, 180, 190,
            200, 210, 220, 230, 240, 250, 260, 270, 280, 290,
            300
        ];
    }
    
    // HPオプションを同期（最小値 <= 最大値になるように）
syncHpOptions() {
    const hpMinSelect = document.getElementById('hpMin');
    const hpMaxSelect = document.getElementById('hpMax');
    
    if (!hpMinSelect || !hpMaxSelect) return;
    
    const currentMin = hpMinSelect.value ? parseInt(hpMinSelect.value) : null;
    const currentMax = hpMaxSelect.value ? parseInt(hpMaxSelect.value) : null;
    
    // 最小値が設定されている場合、最大値のオプションを制限
    if (currentMin !== null) {
        const maxOptions = hpMaxSelect.querySelectorAll('option');
        maxOptions.forEach(option => {
            if (option.value === '') return; // 上限なしは常に表示
            const value = parseInt(option.value);
            option.style.display = value >= currentMin ? '' : 'none';
        });
    } else {
        // 最小値が未設定の場合は全て表示
        const maxOptions = hpMaxSelect.querySelectorAll('option');
        maxOptions.forEach(option => {
            option.style.display = '';
        });
    }
    
    // 最大値が設定されている場合、最小値のオプションを制限
    if (currentMax !== null) {
        const minOptions = hpMinSelect.querySelectorAll('option');
        minOptions.forEach(option => {
            if (option.value === '') return; // 下限なしは常に表示
            const value = parseInt(option.value);
            option.style.display = value <= currentMax ? '' : 'none';
        });
    } else {
        // 最大値が未設定の場合は全て表示
        const minOptions = hpMinSelect.querySelectorAll('option');
        minOptions.forEach(option => {
            option.style.display = '';
        });
    }
    
    // 現在選択されている値が無効な場合、自動調整
    if (currentMin !== null && currentMax !== null && currentMin > currentMax) {
        hpMinSelect.value = currentMax;
        hpMaxSelect.value = currentMin;
        this.syncHpOptions(); // 再帰的に同期
    }
}

    toggleFilterButton(button, filterType, filterValue) {
        // カードの種類フィルターの特別処理（単一選択）
        if (filterType === 'cardType') {
            document.querySelectorAll(`.filter-btn[data-type="cardType"]`).forEach(btn => {
                btn.classList.remove('active');
            });
            
            // 選択されたボタンにactiveクラスを追加
            button.classList.add('active');
            
            // フィルター値を更新
            if (filterValue === 'all') {
                this.currentFilters.cardType = [];
            } else {
                this.currentFilters.cardType = [filterValue];
            }
        } else {
            // その他のフィルターは従来通り複数選択
            const currentIndex = this.currentFilters[filterType].indexOf(filterValue);
            
            if (currentIndex > -1) {
                this.currentFilters[filterType].splice(currentIndex, 1);
                button.classList.remove('active');
            } else {
                this.currentFilters[filterType].push(filterValue);
                button.classList.add('active');
            }
        }
        
        // ★★★ ここでデバウンス版の検索を実行 ★★★
        this.performFilteredSearch();
    }

    normalizeCardTypeValue(value) {
        const normalizationMap = {
            'pokemon': 'Pokémon',
            'trainer': 'Trainer'
        };
        
        return normalizationMap[value.toLowerCase()] || value;
    }
    
performSearch() {
    const query = document.getElementById('cardSearch').value.toLowerCase();
    
    // 現在の検索IDを更新（古い非同期処理を無視するため）
    const searchId = ++this.currentSearchId;
    
    console.log('🔍 検索開始:', {
        query: query,
        filters: this.currentFilters
    });

    const filteredCards = this.cardData.filter(card => {
        // 1. 名前検索
        const matchesQuery = !query || card['名前'].toLowerCase().includes(query);
        
        // 2. タイプ (草、火など)
        const matchesType = this.currentFilters.type.length === 0 || 
                           this.currentFilters.type.includes(card['タイプ']);
        
        // 3. カード分類 (Pokémon, Trainer)
        const matchesCardType = this.currentFilters.cardType.length === 0 || 
                               this.currentFilters.cardType.includes('all') ||
                               this.currentFilters.cardType.includes(card['カードの種類']);

        // 4. レアリティ (rarity_types配列をチェック)
        const matchesRarity = this.currentFilters.rarity.length === 0 || 
                             (card['レア度'] && card['レア度'].rarity_types && 
                              card['レア度'].rarity_types.some(r => this.currentFilters.rarity.includes(r)));

        // 5. HP フィルター
        let matchesHp = true;
        if (card['カードの種類'] === 'Pokémon') {
            const hp = parseInt(card['HP']) || 0;
            if (this.currentFilters.hpMin !== null) matchesHp = matchesHp && hp >= this.currentFilters.hpMin;
            if (this.currentFilters.hpMax !== null) matchesHp = matchesHp && hp <= this.currentFilters.hpMax;
        }

        // 6. パックフィルター
        const matchesPack = this.currentFilters.pack.length === 0 || 
                           (card._packKey && this.currentFilters.pack.includes(card._packKey));

        // 7. 特殊フィルター (Other Filters / Mega, ex, Ability 等)
        const matchesOther = this.currentFilters.other.length === 0 || this.currentFilters.other.every(filter => {
            if (filter === 'ability') return card['特性'] && card['特性'] !== 'None' && card['特性'] !== '';
            if (filter === 'no-ability') return !card['特性'] || card['特性'] === 'None' || card['特性'] === '';
            
            // --- 修正箇所: Mega判定 ---
            if (filter === 'mega') {
                const specialRules = card['特別ルール'] || [];
                // 名前に "Mega" が含まれるかではなく、特別ルールの中に "Mega" があるか
                return Array.isArray(specialRules) ? specialRules.includes('Mega') : specialRules === 'Mega';
            }

            // --- 修正箇所: ex判定 (名前の部分一致だと "Exec" 等に反応するため) ---
            if (filter === 'ex') {
                const specialRules = card['特別ルール'] || [];
                return (Array.isArray(specialRules) && specialRules.includes('ex')) || card['名前'].endsWith(' ex');
            }

            if (filter === 'baby') return card['進化ステージ'] === 'Baby';
            if (filter === 'ultra-beast') {
                const specialRules = card['特別ルール'] || [];
                return Array.isArray(specialRules) && specialRules.includes('Ultra Beast');
            }
            return true;
        });

        // 8. トレーナーズ種別
        const matchesTrainer = this.currentFilters.trainer.length === 0 || 
                              (card['分類'] && this.currentFilters.trainer.includes(card['分類'].toLowerCase()));

        return matchesQuery && matchesType && matchesCardType && matchesRarity && 
               matchesHp && matchesPack && matchesOther && matchesTrainer;
    });

    // 非同期処理の整合性チェック
    if (searchId !== this.currentSearchId) return;

    this.currentSearchResults = filteredCards;
    this.displayedCards = 0;
    this.hasMoreCards = true;

    // 結果表示エリアをクリアして描画
    const container = document.getElementById('resultsContainer');
    if (container) {
        container.innerHTML = '';
        this.loadMoreCards();
    }
}


performFilteredSearch() {
    if (this.searchTimer) {
        cancelAnimationFrame(this.searchTimer); // clearTimeout → cancelAnimationFrame
    }
    
    const searchId = ++this.currentSearchId;
    
    // requestAnimationFrameを使用してよりスムーズに
    this.searchTimer = requestAnimationFrame(() => {
        const searchInput = document.getElementById('cardSearch');
        const searchTerm = searchInput ? searchInput.value : '';
        this.handleSearch(searchTerm, searchId);
    });
}
    
resetSearch() {
    const searchInput = document.getElementById('cardSearch');
    if (searchInput) {
        searchInput.value = '';
    }
    
    // すべてのデバウンスタイマーをクリア
    if (this.searchTimer) {
        clearTimeout(this.searchTimer);
        this.searchTimer = null;
    }
    
    // 新しい検索IDを生成して即時実行
    const searchId = ++this.currentSearchId;
    
    // 即時実行（遅延なし）
    this.handleSearch('', searchId);
}
    
handleSearch(searchTerm, searchId = 0) {
    // 古い検索結果を無視するためにIDチェック
    if (searchId < this.currentSearchId) {
        return;
    }
    
    // 即座にローディング状態を表示
    this.showLoadingState();
    
    // 即座に結果数をクリア
    this.clearResultsCount();
    
    // 即座に結果コンテナをクリア
    const resultsContainer = document.getElementById('resultsContainer');
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
    }
    
    // 非同期でフィルタリング
    setTimeout(() => {
        const results = this.cardData.filter(card => {
            // テキスト検索（カード名のみ）
            let textMatch = true;
            if (searchTerm.trim() !== '') {
                const name = card['名前'] || '';
                const nameMatch = name.toLowerCase().includes(searchTerm.toLowerCase());
                textMatch = nameMatch;
            }
            
            // タイプフィルター
            const typeFilterMatch = this.currentFilters.type.length === 0 || 
                                   this.currentFilters.type.includes(card['タイプ']);
            
            // カードの種類フィルター - ★★★ 修正箇所 ★★★
            const cardTypeFilterMatch = this.currentFilters.cardType.length === 0 || 
                                       this.currentFilters.cardType.includes('all') ||
                                       this.currentFilters.cardType.some(filterType => {
                                           const normalizedFilter = filterType.toLowerCase().trim();
                                           const normalizedCardType = (card['カードの種類'] || '').toLowerCase().trim();
                                           return normalizedFilter === normalizedCardType;
                                       });
            
            // レアリティフィルター
            const rarityFilterMatch = this.currentFilters.rarity.length === 0 || 
                                     this.currentFilters.rarity.includes(this.getRarityText(card));
            console.log(`レア度: ${card['名前']} = "${this.getRarityText(card)}"`);
            
            // HPフィルター
            const hpFilterMatch = this.checkHpFilter(card);
            
            // その他フィルター
            const otherFilterMatch = this.checkOtherFilter(card);
            
            // トレーナーズフィルター
            const trainerFilterMatch = this.checkTrainerFilter(card);
            
            // ワザダメージフィルター
            const damageFilterMatch = this.checkDamageFilter(card);
            
            // 拡張パックフィルター
            const packFilterMatch = this.checkPackFilter(card);
            
            // 「その他」フィルターがある場合、トレーナーズカードは除外
            const excludeTrainerForOtherFilter = this.excludeTrainerForOtherFilter(card);
            
            // 「トレーナーズ」フィルターがある場合、ポケモンカードは除外
            const excludePokemonForTrainerFilter = this.excludePokemonForTrainerFilter(card);
            
            // すべての必須フィルターが一致しているかチェック
            const allFiltersMatch = textMatch && 
                                    typeFilterMatch && 
                                    cardTypeFilterMatch && 
                                    rarityFilterMatch && 
                                    hpFilterMatch && 
                                    otherFilterMatch && 
                                    trainerFilterMatch && 
                                    damageFilterMatch && 
                                    packFilterMatch &&
                                    excludeTrainerForOtherFilter &&
                                    excludePokemonForTrainerFilter;
            
            return allFiltersMatch;
        });
        
        console.log(`📊 フィルタリング結果: ${results.length}件`);
        
        // 最後のIDチェック
        if (searchId < this.currentSearchId) {
            console.log(`⏭️ 検索完了時点で新しい検索が開始されました (${searchId} → ${this.currentSearchId})`);
            return;
        }
        
        // 結果数を即時更新
        this.updateResultsCount(results.length, this.cardData.length);
        
        // 無限スクロール用に結果を保存
        this.currentSearchResults = results;
        this.displayedCards = 0;
        this.hasMoreCards = results.length > 0;
        
        // 最初のバッチのカードを表示
        this.showFirstBatchOfResults(results);
        console.log('🔍 === handleSearch 終了 ===');
    }, 50);
}

    excludePokemonForTrainerFilter(card) {
    // 「トレーナーズ」フィルターが選択されていない場合は常に true
    if (this.currentFilters.trainer.length === 0) {
        return true;
    }
    
    // カードがポケモンカードかチェック
    const isPokemonCard = card['カードの種類'] === 'Pokémon';
    
    // ポケモンカードでない場合は OK
    if (!isPokemonCard) {
        return true;
    }
    
    // ポケモンカードの場合は NG
    console.log(`❌ ${card['名前']}: トレーナーズフィルター選択中はポケモンカードを除外`);
    return false;
}

excludeTrainerForOtherFilter(card) {
    // 現在2回定義されているこのメソッドを1つに
    if (this.currentFilters.other.length === 0) return true;
    
    const isTrainerCard = card['カードの種類'] === 'Trainer';
    if (!isTrainerCard) return true;
    
    console.log(`❌ ${card['名前']}: その他フィルター選択中はトレーナーズカードを除外`);
    return false;
}

checkPackFilter(card) {
    if (this.currentFilters.pack.length === 0) {
        return true;
    }
    
    const cardPackKey = card._packKey;
    const cardPackNames = this.getAllCardPacks(card);
    const cardSets = card['収録セット'] || [];
    const normalizedCardPackNames = cardPackNames.map(name => this.normalizePackName(name));
    const acquisitionMethods = card['入手方法'] || [];
    
    // シークレットミッションチェック（英語版）
    const hasSecretMission = acquisitionMethods.some(method => 
        method && typeof method === 'string' && method.includes('Secret mission')
    );
    
    // Promoカードかどうかを先に判定
    const isPromoCard = cardSets.some(set => 
        set && typeof set === 'string' && set.toLowerCase().includes('promo')
    ) || cardPackKey === 'Promo';
    
    const result = this.currentFilters.pack.some(selected => {
        console.log(`\n  ▼ 選択: "${selected}"`);
        
        // Promo特別処理
        if (selected === 'Promo' && isPromoCard) {
            return true;
        }
        // 1. 選択がパックキーかパック名かを判定
        const isKey = this.isPackKey(selected);
        let selectedPackKey = selected;
        
        // パック名の場合、パックキーに変換
        if (!isKey) {
            selectedPackKey = this.getPackKeyFromPackName(selected);
        }
        
        // 2. パックキー比較
        if (cardPackKey !== selectedPackKey) {
            return false;
        }
        
        // シークレットミッションがある場合は常にtrue
        if (hasSecretMission) {
            return true;
        }
        
        // 3. パック名比較（パック名選択の場合のみ）
        if (!isKey) {
            const normalizedSelectedName = this.normalizePackName(selected); // 選択されたパック名
            const hasMatchingPackName = normalizedCardPackNames.includes(normalizedSelectedName);
            
            if (hasMatchingPackName) {
                return true;
            } else {
                return false;
            }
        } else {
            return true;
        }
    });
    
    return result;
}

// 新しいメソッド: パックキーかどうか判定
isPackKey(value) {
    // パックキーのパターン（例: a1, a4b, b1 など）
    const packKeyPattern = /^[a-z]\d+[a-z]?$/i;
    return packKeyPattern.test(value);
}

// 新しいメソッド: パック名一致チェック
checkPackNameMatch(selectedName, cardPackNames) {
    // 正規化して比較
    const normalizedSelected = this.normalizePackName(selectedName);
    const normalizedCardNames = cardPackNames.map(name => this.normalizePackName(name));
    
    return normalizedCardNames.includes(normalizedSelected);
}

// パック名からパックキーを取得
getPackKeyFromPackName(packName) {
    if (!this.packData) return null;
    
    const normalizedInput = this.normalizePackName(packName); // 同じ正規化
    
    for (const [packKey, seriesData] of Object.entries(this.packData)) {
        if (seriesData.packs) {
            for (const pack of seriesData.packs) {
                const normalizedPack = this.normalizePackName(pack); // 同じ正規化
                if (normalizedPack === normalizedInput) {
                    return packKey;
                }
            }
        }
    }
    
    return null;
}

// 正規化関数（必要に応じて調整）// この関数を統一版に修正するだけ
normalizePackName(packName) {
    if (!packName) return '';
    
    return packName
        .toString()
        .trim()
        .toLowerCase()
        .replace(/[:：]/g, '')      // コロン除去
        .replace(/pack/gi, '')      // "pack"除去
        .replace(/\s+/g, ' ')      // 空白正規化
        .trim();
}


// getAllCardPacksも正規化対応
getAllCardPacks(card) {
    const acquisitionMethods = card['入手方法'] || [];
    const cardSets = card['収録セット'] || [];
    const packs = [];
    
    // Promoカードか判定
    const isPromoCard = cardSets.some(set => 
        set && typeof set === 'string' && set.toLowerCase().includes('promo')
    );
    
    // Promoカードなら収録セット、そうでなければ入手方法を使う
    const source = isPromoCard ? cardSets : acquisitionMethods;
    
    source.forEach(item => {
        if (typeof item === 'string') {
            let packName;
            if (isPromoCard) {
                // 収録セットから：そのまま使用
                packName = item.trim();
            } else {
                // 入手方法から："パック: "を除去
                if (item.startsWith('パック: ')) {
                    packName = item.replace('パック: ', '').trim();
                }
            }
            
            if (packName && !packs.includes(packName)) {
                packs.push(packName);
            }
        }
    });
    
    return packs;
}

// Deluxe Pack のバリエーションかチェック
isDeluxePackVariant(packName) {
    if (!packName) return false;
    
    const lowerName = packName.toLowerCase();
    return (
        lowerName.includes('deluxe') && 
        lowerName.includes('pack') && 
        lowerName.includes('ex')
    );
}

// またはより具体的に
isDeluxePackVariant(packName) {
    if (!packName) return false;
    
    const normalized = packName.toLowerCase()
        .replace(/\s*:\s*/g, ' ')    // コロンをスペースに
        .replace(/\s+/g, ' ')        // 空白を正規化
        .trim();
    
    const deluxeVariants = [
        'deluxe pack ex',
        'deluxe pack ex pack',
        'deluxe pack: ex'
    ];
    
    return deluxeVariants.includes(normalized);
}

  getCardPack(card) {
      // 入手方法から拡張パック情報を抽出
      const acquisitionMethods = card['入手方法'] || [];
      
      console.log('🔍 getCardPack() 処理開始');
      console.log('   カード名:', card['名前']);
      console.log('   入手方法配列:', acquisitionMethods);
      
      // "パック: "で始まる行からパック名を抽出
      for (const method of acquisitionMethods) {
          if (typeof method === 'string' && method.startsWith('パック: ')) {
              const packName = method.replace('パック: ', '').trim();
              
              console.log(`   抽出成功: "${packName}"`);
              console.log(`   getCardPack() 結果: "${packName}"`);
              console.log('🔍 getCardPack() 処理終了');
              
              return packName;
          }
      }
      
      // デフォルトの拡張パックフィールドもチェック
      const defaultPack = card['拡張パック'] || card['pack'] || card['拡張パック名'] || '';
      
      if (defaultPack) {
          console.log(`   デフォルトフィールドから取得: "${defaultPack}"`);
      } else {
          console.log('   パック情報が見つかりません');
      }
      
      console.log('🔍 getCardPack() 処理終了');
      return defaultPack;
}
  

// カードの入手可能パックを取得（プロモーション対応版）
getAllCardPacksForFilter(card) {
    const acquisitionMethods = card['入手方法'] || [];
    const cardPacks = card['収録セット'] || [];
    const packs = [];
    
    // 収録セットに"promo"が含まれている場合（プロモーションカード）
    const hasPromoInSet = cardPacks.some(pack => 
        typeof pack === 'string' && pack.toLowerCase().includes('promo')
    );
    
    if (hasPromoInSet) {
        // プロモーションカードの場合：収録セットから取得
        this.getPacksFromSet(cardPacks, packs);
    } else {
        // 通常カードの場合：入手方法から取得
        this.getPacksFromAcquisitionMethods(acquisitionMethods, packs);
    }
    
    return packs;
}

// 収録セットからパックを取得（プロモーションカード用）
getPacksFromSet(cardPacks, packsArray) {
    if (!Array.isArray(cardPacks)) return;
    
    cardPacks.forEach(packName => {
        if (packName && typeof packName === 'string') {
            const cleanName = packName.trim();
            if (cleanName && !packsArray.includes(cleanName)) {
                packsArray.push(cleanName);
            }
        }
    });
}

// 入手方法からパックを取得（通常カード用）
getPacksFromAcquisitionMethods(acquisitionMethods, packsArray) {
    if (!Array.isArray(acquisitionMethods)) return;
    
    acquisitionMethods.forEach(method => {
        if (typeof method === 'string' && method.startsWith('パック: ')) {
            const packName = method.replace('パック: ', '').trim();
            
            // ★★★ 修正ここから ★★★
            // 以前のバグったコード: const cleanPackName = packName.split(':')[0].trim();
            // これだと "Deluxe Pack: ex" → "Deluxe Pack" になってしまう
            
            // 修正後: 完全なパック名を使用
            const cleanPackName = packName; // 分割しない！
            // ★★★ 修正ここまで ★★★
            
            if (cleanPackName && !packsArray.includes(cleanPackName)) {
                packsArray.push(cleanPackName);
                console.log(`   📦 入手方法から追加: "${cleanPackName}"`);
            }
        }
    });
}
  
// パック名を比較用に正規化
normalizePackNameForComparison(packName) {
    if (!packName) return '';
    
    // すべての空白を除去して小文字化
    let normalized = packName
        .toLowerCase()
        .replace(/\s+/g, ''); // 全ての空白を除去
    
    console.log(`📝 正規化: "${packName}" → "${normalized}"`);
    
    return normalized;
}

// 拡張パックフィルターを適用
applyPackFilter() {
    console.log('🔄 applyPackFilter() 開始');
    console.log('   現在のパックフィルター:', this.currentFilters.pack);
    
    // Bulbasaurのデータを使ってテスト
    const bulbasaur = this.cardData.find(card => card['名前'] === 'Bulbasaur');
    if (bulbasaur) {
        console.log('   Bulbasaurの入手可能パック:', this.getAllCardPacks(bulbasaur));
        console.log('   Bulbasaurがフィルターにマッチするか?:', this.checkPackFilter(bulbasaur));
    }
    
    this.performFilteredSearch();
    console.log('🔄 applyPackFilter() 終了');
}
    
    // HPフィルターをリセット
resetHpFilter() {
    const hpMinSelect = document.getElementById('hpMin');
    const hpMaxSelect = document.getElementById('hpMax');
    
    if (hpMinSelect) hpMinSelect.value = '';
    if (hpMaxSelect) hpMaxSelect.value = '';
    
    this.currentFilters.hpMin = null;
    this.currentFilters.hpMax = null;
    
    // オプションをリセット
    this.syncHpOptions();
    
    console.log('HPフィルターをリセット');
    
    // この行を追加！！！リセット後も検索を実行
    this.performFilteredSearch();
}
    
    // HPフィルターのチェック
checkHpFilter(card) {
    console.log(`🔍 checkHpFilter - カード: ${card['名前']}, 種類: ${card['カードの種類']}, HP: ${JSON.stringify(card['HP'])}, 分類: ${card['分類']}`);
    
    const hpRaw = card['HP'];
    
    const hpMin = this.currentFilters.hpMin;
    const hpMax = this.currentFilters.hpMax;
    
    console.log(`⚙️ ${card['名前']}: HPフィルター設定: min=${hpMin}, max=${hpMax}`);
    
    // フィルターが設定されていない場合は全て表示
    if (hpMin === null && hpMax === null) {
        console.log(`✅ ${card['名前']}: HPフィルターなしなので true`);
        return true;
    }
    
    // ★★★ HPフィールドがないカードは表示しない ★★★
    if (hpRaw === undefined || hpRaw === null || hpRaw === '') {
        console.log(`❌ ${card['名前']}: HPフィールドがないので false`);
        return false;
    }
    
    // HPを数値として取得
    let hpValue;
    if (typeof hpRaw === 'string') {
        hpValue = parseInt(hpRaw, 10);
        if (isNaN(hpValue)) {
            hpValue = 0;
            console.log(`⚠️ ${card['名前']}: HP文字列を数値に変換できません: "${hpRaw}"`);
        }
    } else if (typeof hpRaw === 'number') {
        hpValue = hpRaw;
    } else {
        hpValue = 0;
        console.log(`⚠️ ${card['名前']}: HPの型が不正: ${typeof hpRaw}`);
    }
    
    console.log(`🔢 ${card['名前']}: HP数値 = ${hpValue}`);
    
    // HPが0のカードはHPフィルターが設定されている場合、表示しない
    if (hpValue === 0) {
        console.log(`❌ ${card['名前']}: HPが0なので false`);
        return false;
    }
    
    // 最小値のみ設定されている場合
    if (hpMin !== null && hpMax === null) {
        const result = hpValue >= hpMin;
        console.log(`📊 ${card['名前']}: 最小値チェック ${hpValue} >= ${hpMin} = ${result}`);
        return result;
    }
    
    // 最大値のみ設定されている場合
    if (hpMin === null && hpMax !== null) {
        const result = hpValue <= hpMax;
        console.log(`📊 ${card['名前']}: 最大値チェック ${hpValue} <= ${hpMax} = ${result}`);
        return result;
    }
    
    // 両方設定されている場合
    if (hpMin !== null && hpMax !== null) {
        const result = hpValue >= hpMin && hpValue <= hpMax;
        console.log(`📊 ${card['名前']}: 範囲チェック ${hpMin} <= ${hpValue} <= ${hpMax} = ${result}`);
        return result;
    }
    
    console.log(`✅ ${card['名前']}: デフォルトで true`);
    return true;
}

applyHpFilter() {
    const hpMinSelect = document.getElementById('hpMin');
    const hpMaxSelect = document.getElementById('hpMax');
    
    let hpMin = hpMinSelect ? hpMinSelect.value : '';
    let hpMax = hpMaxSelect ? hpMaxSelect.value : '';
    
    // 空文字列の場合は null に変換
    hpMin = hpMin === '' ? null : parseInt(hpMin);
    hpMax = hpMax === '' ? null : parseInt(hpMax);
    
    // NaNチェック（数値でない場合は null）
    hpMin = isNaN(hpMin) ? null : hpMin;
    hpMax = isNaN(hpMax) ? null : hpMax;
    
    // フィルターを更新
    this.currentFilters.hpMin = hpMin;
    this.currentFilters.hpMax = hpMax;
    
    console.log('HPフィルターを適用:', { hpMin, hpMax });
    this.performFilteredSearch();
}
  
  // ワザーのセットアップを追加
    setupDamageFilter() {
        this.generateDamageOptions();
        
        const damageMinSelect = document.getElementById('damageMin');
        const damageMaxSelect = document.getElementById('damageMax');
        
        if (damageMinSelect) {
            damageMinSelect.addEventListener('change', () => {
                this.syncDamageOptions();
                this.applyDamageFilter();
            });
        }
        
        if (damageMaxSelect) {
            damageMaxSelect.addEventListener('change', () => {
                this.syncDamageOptions();
                this.applyDamageFilter();
            });
        }
    }

    // ワザダメージオプションを動的に生成
    generateDamageOptions() {
        const damageOptions = this.getDamageOptions();
        const damageMinSelect = document.getElementById('damageMin');
        const damageMaxSelect = document.getElementById('damageMax');
        
        if (!damageMinSelect || !damageMaxSelect) return;
        
        // 最小値用のオプションを生成
        damageMinSelect.innerHTML = '<option value="">No min</option>';
        damageOptions.forEach(damage => {
            damageMinSelect.innerHTML += `<option value="${damage}">${damage}</option>`;
        });
        
        // 最大値用のオプションを生成
        damageMaxSelect.innerHTML = '<option value="">No max</option>';
        damageOptions.forEach(damage => {
            damageMaxSelect.innerHTML += `<option value="${damage}">${damage}</option>`;
        });
        // 最大値用に300を追加
        damageMaxSelect.innerHTML += '<option value="300">300</option>';
    }

    // ワザダメージオプションの値を定義
    getDamageOptions() {
        return [
            0, 10, 20, 30, 40, 50, 60, 70, 80, 90,
            100, 110, 120, 130, 140, 150, 160, 170, 180, 190,
            200, 210, 220, 230, 240, 250, 260, 270, 280, 290,
            300
        ];
    }

    // ワザダメージオプションを同期
    syncDamageOptions() {
        const damageMinSelect = document.getElementById('damageMin');
        const damageMaxSelect = document.getElementById('damageMax');
        
        if (!damageMinSelect || !damageMaxSelect) return;
        
        const currentMin = damageMinSelect.value ? parseInt(damageMinSelect.value) : null;
        const currentMax = damageMaxSelect.value ? parseInt(damageMaxSelect.value) : null;
        
        // 最小値が設定されている場合、最大値のオプションを制限
        if (currentMin !== null) {
            const maxOptions = damageMaxSelect.querySelectorAll('option');
            maxOptions.forEach(option => {
                if (option.value === '') return;
                const value = parseInt(option.value);
                option.style.display = value >= currentMin ? '' : 'none';
            });
        } else {
            const maxOptions = damageMaxSelect.querySelectorAll('option');
            maxOptions.forEach(option => {
                option.style.display = '';
            });
        }
        
        // 最大値が設定されている場合、最小値のオプションを制限
        if (currentMax !== null) {
            const minOptions = damageMinSelect.querySelectorAll('option');
            minOptions.forEach(option => {
                if (option.value === '') return;
                const value = parseInt(option.value);
                option.style.display = value <= currentMax ? '' : 'none';
            });
        } else {
            const minOptions = damageMinSelect.querySelectorAll('option');
            minOptions.forEach(option => {
                option.style.display = '';
            });
        }
        
        // 現在選択されている値が無効な場合、自動調整
        if (currentMin !== null && currentMax !== null && currentMin > currentMax) {
            damageMinSelect.value = currentMax;
            damageMaxSelect.value = currentMin;
            this.syncDamageOptions();
        }
    }

    // ワザーを適用
    applyDamageFilter() {
        const damageMinSelect = document.getElementById('damageMin');
        const damageMaxSelect = document.getElementById('damageMax');
        
        let damageMin = damageMinSelect ? damageMinSelect.value : '';
        let damageMax = damageMaxSelect ? damageMaxSelect.value : '';
        
        damageMin = damageMin === '' ? null : parseInt(damageMin);
        damageMax = damageMax === '' ? null : parseInt(damageMax);
        
        damageMin = isNaN(damageMin) ? null : damageMin;
        damageMax = isNaN(damageMax) ? null : damageMax;
        
        this.currentFilters.damageMin = damageMin;
        this.currentFilters.damageMax = damageMax;
        
        this.performFilteredSearch();
    }

    // ワザーをリセット
    resetDamageFilter() {
        const damageMinSelect = document.getElementById('damageMin');
        const damageMaxSelect = document.getElementById('damageMax');
        
        if (damageMinSelect) damageMinSelect.value = '';
        if (damageMaxSelect) damageMaxSelect.value = '';
        
        this.currentFilters.damageMin = null;
        this.currentFilters.damageMax = null;
        
        this.syncDamageOptions();
    }
  
// ワザーのチェック（ダメージデータがないカードを除外）
checkDamageFilter(card) {
    
    const damageMin = this.currentFilters.damageMin;
    const damageMax = this.currentFilters.damageMax;
    
    console.log(`⚙️ ${card['名前']}: ー設定: min=${damageMin}, max=${damageMax}`);
    
    // フィルターが設定されていない場合は全て表示
    if (damageMin === null && damageMax === null) {
        console.log(`✅ ${card['名前']}: ーなしなので true`);
        return true;
    }
    
    // カードの最大ダメージを取得
    const maxDamage = this.getMaxDamage(card);
    
    console.log(`📊 ${card['名前']}: 最大ダメージ = ${maxDamage}`);
    
    // ダメージが0（ダメージデータなし）の場合
    if (maxDamage === 0) {
        console.log(`❌ ${card['名前']}: ダメージデータがないので false`);
        return false;
    }
    
    // 最小値のみ設定されている場合
    if (damageMin !== null && damageMax === null) {
        const result = maxDamage >= damageMin;
        console.log(`📊 ${card['名前']}: 最小値チェック ${maxDamage} >= ${damageMin} = ${result}`);
        return result;
    }
    
    // 最大値のみ設定されている場合
    if (damageMin === null && damageMax !== null) {
        const result = maxDamage <= damageMax;
        console.log(`📊 ${card['名前']}: 最大値チェック ${maxDamage} <= ${damageMax} = ${result}`);
        return result;
    }
    
    // 両方設定されている場合
    const result = maxDamage >= damageMin && maxDamage <= damageMax;
    console.log(`📊 ${card['名前']}: 範囲チェック ${damageMin} <= ${maxDamage} <= ${damageMax} = ${result}`);
    return result;
}

// カードの最大ワザダメージを取得（改良版）
getMaxDamage(card) {
    console.log(`🔍 getMaxDamage - カード: ${card['名前']}, 種類: ${card['カードの種類']}`);
    
    const moves = card['ワザ'] || [];
    let maxDamage = 0;
    let hasValidDamage = false;
    
    console.log(`📊 ${card['名前']}: ワザ数 = ${moves.length}`);
    
    if (Array.isArray(moves) && moves.length > 0) {
        moves.forEach((move, index) => {
            if (move && move['ダメージ']) {
                const damageStr = move['ダメージ'];
                
                // ダメージ値が"N/A"や空の場合はスキップ
                if (damageStr === 'N/A' || damageStr === '' || damageStr === null || damageStr === undefined) {
                    console.log(` ワザ${index}: ${move['名前']}, ダメージ: "${damageStr}" (無効値)`);
                    return;
                }
                
                // 数値に変換
                const damage = parseInt(damageStr, 10);
                
                if (!isNaN(damage)) {
                    console.log(` ワザ${index}: ${move['名前']}, ダメージ: "${damageStr}" → 数値: ${damage}`);
                    if (damage > maxDamage) {
                        maxDamage = damage;
                    }
                    hasValidDamage = true;
                } else {
                    console.log(` ワザ${index}: ${move['名前']}, ダメージ: "${damageStr}" (数値変換不可)`);
                }
            } else if (move) {
                console.log(` ワザ${index}: ${move['名前']}, ダメージフィールドなし`);
            }
        });
    } else {
        console.log(`📊 ${card['名前']}: ワザデータがありません`);
    }
    
    // 有効なダメージデータが見つからない場合は0を返す
    if (!hasValidDamage) {
        console.log(`📊 ${card['名前']}: 有効なダメージデータなし → 0`);
        return 0;
    }
    
    console.log(`📊 ${card['名前']}: 最終最大ダメージ = ${maxDamage}`);
    return maxDamage;
}
  
    // その他フィルターのチェック
    checkOtherFilter(card) {
    if (this.currentFilters.other.length === 0) {
        return true;
    }
    
    // 各フィルター条件をチェック
    return this.currentFilters.other.some(filter => {
        switch (filter) {
            case 'ability':
                    return this.hasAbility(card);
                case 'no-ability':
                    return !this.hasAbility(card);
                case 'ex':
                    return this.isExPokemon(card);
                case 'ultra-beast':
                    return this.isUltraBeast(card);
                case 'mega':
                    return this.isMegaEvolution(card);
                case 'baby': // Baby Pokémon ケースを追加
                    return this.isBabyPokemon(card);
                default:
                    return true;
        }
    });
}
    
    // 特性があるかチェック
    hasAbility(card) {
        const ability = card['特性'] || [];
        // 配列の場合、空でないかチェック
        if (Array.isArray(ability)) {
            return ability.length > 0;
        }
        // 文字列の場合、空文字でないかチェック
        return ability.trim() !== '';
    }
    
// メガシンカexかチェック（特別ルールから判別）
isMegaEvolution(card) {
    const rules = card['特別ルール'] || '';
    return rules.includes('Mega') || rules.includes('メガ');
}

// Baby Pokémon かチェック（特別ルールから判別）
isBabyPokemon(card) {
    const rules = card['特別ルール'] || '';
    return rules.includes('Baby') || rules.includes('ベイビー');
}

// Pokémon ex かチェック（特別ルールから判別）
isExPokemon(card) {
    const rules = card['特別ルール'] || '';
    return rules.includes('ex');
}

// ウルトラビーストかチェック（特別ルールから判別）
isUltraBeast(card) {
    const rules = card['特別ルール'] || '';
    return rules.includes('Ultra Beast') || rules.includes('ウルトラビースト');
}
    
    // トレーナーズフィルターのチェック
    checkTrainerFilter(card) {
        if (this.currentFilters.trainer.length === 0) {
            return true;
        }
        
        // トレーナーカード以外は対象外（ただし他のフィルターには影響しない）
        if (card['カードの種類'] !== 'Trainer') {
            return true;  // false → true に変更
        }
        
        // 各トレーナーフィルター条件をチェック
        return this.currentFilters.trainer.some(filter => {
            switch (filter) {
                case 'item':
                    return this.isItemCard(card);
                case 'tool':
                    return this.isToolCard(card);
                case 'fossil':
                    return this.isFossilCard(card);
                case 'support':
                    return this.isSupportCard(card);
                default:
                    return true;
            }
        });
    }

    // グッズカードかチェック
    isItemCard(card) {
        const category = card['分類'] || '';
        const name = card['名前'] || '';
        // 「分類」フィールドが「Item」または名前に「グッズ」が含まれる
        return category === 'Item' || name.includes('グッズ');
    }
    
    // ポケモンのどうぐかチェック
    isToolCard(card) {
        const category = card['分類'] || '';
        const name = card['名前'] || '';
        // 「分類」フィールドが「Tool」または名前に「どうぐ」が含まれる
        return category === 'Tool' || name.includes('どうぐ');
    }
    
    // グッズ(化石)かチェック
    isFossilCard(card) {
        const category = card['分類'] || '';
        const name = card['名前'] || '';
        // 「分類」フィールドが「Fossil」または名前に「化石」が含まれる
        return category === 'Fossil' || name.includes('化石');
    }
    
    // サポートカードかチェック
    isSupportCard(card) {
        const category = card['分類'] || '';
        const name = card['名前'] || '';
        // 「分類」フィールドが「Supporter」または名前に「サポート」が含まれる
        return category === 'Supporter' || name.includes('サポート');
}
    
    areFiltersEmpty() {
        const basicFiltersEmpty = Object.values({
            type: this.currentFilters.type,
            // cardTypeは「すべて」選択時は空配列なのでそのままチェック
            rarity: this.currentFilters.rarity,
            other: this.currentFilters.other,
            trainer: this.currentFilters.trainer,
            pack: this.currentFilters.pack
        }).every(arr => arr.length === 0);
        
        const hpFiltersEmpty = this.currentFilters.hpMin === null && this.currentFilters.hpMax === null;
        const damageFiltersEmpty = this.currentFilters.damageMin === null && this.currentFilters.damageMax === null;
        
        return basicFiltersEmpty && hpFiltersEmpty && damageFiltersEmpty;
}
    
    getRarityText(card) {
        if (card['レア度'] && card['レア度']['rarity_types'] && card['レア度']['rarity_types'].length > 0) {
            const rarityType = card['レア度']['rarity_types'][0];
            const rarityCount = card['レア度']['count'] || 1;
            return `${rarityType}${rarityCount}`;
        }
        return '';
    }
    
setupPackFilter() {
    this.loadPackData();
    this.setupPackSelectEvents();
}

setupAdvancedFiltersToggle() {
    console.log('🔧 setupAdvancedFiltersToggle() 実行開始');
    
    const toggleButton = document.getElementById('toggleAdvancedFilters');
    const advancedFilters = document.getElementById('advancedFilters');
    
    if (!toggleButton || !advancedFilters) {
        console.error('詳細フィルター要素が見つかりません');
        return;
    }
    
    console.log('✅ 詳細フィルター要素を正常に取得');
    
    // 初期状態を閉じた状態に設定
    advancedFilters.style.display = 'none';
    advancedFilters.style.opacity = '0';
    advancedFilters.style.transform = 'translateY(-10px)';
    toggleButton.classList.remove('active');
    
    const toggleText = toggleButton.querySelector('span:first-child');
    if (toggleText) {
        toggleText.textContent = 'Show Advanced Filters';
    }
    
    console.log('✅ 初期状態: 詳細フィルターを非表示に設定');
    
    // トグルボタンのクリックイベントを設定
    toggleButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('🎯 詳細フィルタートグルボタンがクリックされました');
        
        const isVisible = advancedFilters.style.display === 'block';
        
        if (isVisible) {
            // 閉じるアニメーション
            advancedFilters.style.opacity = '0';
            advancedFilters.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                advancedFilters.style.display = 'none';
                toggleButton.classList.remove('active');
                const textSpan = toggleButton.querySelector('span:first-child');
                if (textSpan) {
                    textSpan.textContent = 'Show Advanced Filters';
                }
                console.log('📌 詳細フィルターを非表示にしました');
            }, 300);
            
        } else {
            // 表示する
            advancedFilters.style.display = 'block';
            advancedFilters.style.opacity = '0';
            advancedFilters.style.transform = 'translateY(-10px)';
            
            // 強制リフロー
            void advancedFilters.offsetWidth;
            
            // 開くアニメーション
            requestAnimationFrame(() => {
                advancedFilters.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                advancedFilters.style.opacity = '1';
                advancedFilters.style.transform = 'translateY(0)';
            });
            
            toggleButton.classList.add('active');
            const textSpan = toggleButton.querySelector('span:first-child');
            if (textSpan) {
                textSpan.textContent = 'Hide Advanced Filters';
            }
            console.log('📌 詳細フィルターを表示しました');
        }
    });
    
    console.log('✅ setupAdvancedFiltersToggle() 実行完了');
}

// 拡張パックデータを読み込む
async loadPackData() {
    try {
        const response = await fetch('/data/pack_set_name.json');
        if (!response.ok) throw new Error('拡張パックデータの読み込みに失敗');
        
        this.packData = await response.json();
        
        console.log('🗺️ 読み込まれたパックデータのキー:', Object.keys(this.packData));
        
        // ★★★ パックキーマッピングを作成 ★★★
        this.packKeyMapping = {};
        this.packNameToKeyMap = {}; // ★★★ 新規追加：パック名→パックキーマッピング ★★★
        
        Object.keys(this.packData).forEach(packKey => {
            const seriesData = this.packData[packKey];
            
            // packKey → set名 のマッピング
            if (seriesData.set) {
                this.packKeyMapping[packKey] = {
                    displayName: seriesData.set,
                    packs: seriesData.packs || []
                };
            }
            
            // ★★★ パック名 → パックキーのマッピングを作成 ★★★
            if (seriesData.packs && Array.isArray(seriesData.packs)) {
                seriesData.packs.forEach(packName => {
                    // 正規化したキーで保存（比較用）
                    const normalizedPackName = this.normalizePackNameForMapping(packName);
                    this.packNameToKeyMap[normalizedPackName] = packKey;
                    
                    // 元のパック名でも保存（高速アクセス用）
                    this.packNameToKeyMap[packName] = packKey;
                });
            }
        });
        
        console.log('🗺️ パックキーマッピング:', this.packKeyMapping);
        console.log('🗺️ パック名→キーマッピング（サンプル）:', 
            Object.entries(this.packNameToKeyMap).slice(0, 5));
        
        this.populatePackSelect();
        
    } catch (error) {
        console.error('❌ 拡張パックデータの読み込みエラー:', error);
        this.packData = {};
        this.packKeyMapping = {};
        this.packNameToKeyMap = {};
        this.populatePackSelect();
    }
}

// ★★★ マッピング用の正規化関数 ★★★
normalizePackNameForMapping(packName) {
    if (!packName) return '';
    
    return packName
        .toString()
        .trim()
        .toLowerCase()
        .replace(/\s+/g, ' ')      // 連続する空白を単一スペースに
        .replace(/\s*:\s*/g, ': ') // コロンの前後の空白を正規化
        .replace(/[　]/g, ' ');    // 全角空白を半角に
}

    // 拡張パック選択肢を生成
populatePackSelect() {
    console.log('🔄 populatePackSelect 開始');
    
    const selectItems = document.querySelector('.pack-selection-group .select-items');
    const selectSelected = document.querySelector('.pack-selection-group .select-selected');
    
    if (!selectItems || !selectSelected) return;
    
    // 既存の内容をクリア
    selectItems.innerHTML = '';
    
    // "All Expansion Sets" オプション
    const allContainer = document.createElement('div');
    allContainer.className = 'series-container';
    
    const allOption = document.createElement('div');
    allOption.className = 'select-item series-option';
    allOption.dataset.value = 'all';
    if (this.currentFilters.pack.length === 0) {
        allOption.classList.add('selected');
    }
    
    allOption.innerHTML = `
        <div class="series-info">
            <span class="series-name" style="font-weight: bold;">All Expansion Sets</span>
        </div>
    `;
    allContainer.appendChild(allOption);
    selectItems.appendChild(allContainer);
    
    // 各シリーズのオプション
    if (this.packData) {
        Object.keys(this.packData).forEach(seriesKey => {
            const seriesData = this.packData[seriesKey];
            const displayName = seriesData.set;
            
            // このシリーズ内の選択済みパック数を計算
            const selectedCount = this.getSelectedPacksCountInSeries(seriesKey);
            const isSeriesSelected = selectedCount === (seriesData.packs ? seriesData.packs.length : 0);
            
            const seriesContainer = document.createElement('div');
            seriesContainer.className = 'series-container';
            
            // シリーズオプション（セット名）
            const seriesOption = document.createElement('div');
            seriesOption.className = 'select-item series-option';
            seriesOption.dataset.value = seriesKey;
            
            if (isSeriesSelected) {
                seriesOption.classList.add('selected');
            }
            
seriesOption.innerHTML = `
    <img src="/images/packs/${seriesData.set}.webp" alt="${seriesData.set}" 
         class="select-icon" onerror="this.style.display='none'">
    <div class="series-info">
        <span class="series-name" style="font-weight: bold;">${seriesData.set}</span>
        <span class="series-key">(${seriesKey.toUpperCase()})</span>
    </div>
`;
            
            seriesContainer.appendChild(seriesOption);
            
            // 個別パックオプション
            if (seriesData.packs) {
                seriesData.packs.forEach(packName => {
                    const packOption = document.createElement('div');
                    packOption.className = 'select-item pack-option';
                    packOption.dataset.value = packName;
                    
                    const isPackSelected = this.currentFilters.pack.includes(packName);
                    if (isPackSelected) {
                        packOption.classList.add('selected');
                    }
                    
                    packOption.innerHTML = `
                        <img src="/images/packs/${packName}.webp" alt="${packName}" 
                             class="select-icon" onerror="this.style.display='none'">
                        <span class="pack-name">${packName}</span>
                        ${isPackSelected ? '<span class="checkmark">✓</span>' : ''}
                    `;
                    seriesContainer.appendChild(packOption);
                });
            }
            
            selectItems.appendChild(seriesContainer);
        });
    }
    
    // 表示を更新
    this.updateSelectedPacksDisplay();
    
    // イベントリスナーを設定
    setTimeout(() => {
        this.setupPackSelectEventsDirectly();
    }, 50);
}

// 新しいヘルパーメソッド: シリーズ内の選択済みパック数を取得
getSelectedPacksCountInSeries(seriesKey) {
    if (!this.packData || !this.packData[seriesKey] || !this.packData[seriesKey].packs) {
        return 0;
    }
    
    const seriesData = this.packData[seriesKey];
    return seriesData.packs.filter(packName => 
        this.currentFilters.pack.includes(packName)
    ).length;
}

setupPackSelectEventsDirectly() {
    console.log('🔧 setupPackSelectEventsDirectly() 開始 - シンプルな実装');
    
    const selectSelected = document.querySelector('.pack-selection-group .select-selected');
    const selectItems = document.querySelector('.pack-selection-group .select-items');
    
    if (!selectSelected || !selectItems) {
        console.error('❌ パック選択要素が見つかりません');
        return;
    }
    
    console.log('✅ パック選択要素を正常に取得');
    
    // ★★★ シンプルな実装：すべてのイベントを一度に設定 ★★★
    
    // 1. 開閉状態のフラグ
    let isDropdownOpen = false;
    
    // 2. ドロップダウンを開閉する関数
    const toggleDropdown = (open) => {
        if (open === undefined) {
            open = !isDropdownOpen;
        }
        
        if (open) {
            // 開く
            selectItems.style.display = 'block';
            selectSelected.classList.add('select-arrow-active');
            isDropdownOpen = true;
            
            // アニメーション
            setTimeout(() => {
                selectItems.style.opacity = '1';
                selectItems.style.transform = 'translateY(0)';
            }, 10);
        } else {
            // 閉じる
            selectItems.style.opacity = '0';
            selectItems.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                selectItems.style.display = 'none';
                selectSelected.classList.remove('select-arrow-active');
                isDropdownOpen = false;
            }, 300);
        }
    };
    
    // 3. 初期状態を閉じた状態に設定
    selectItems.style.display = 'none';
    selectItems.style.opacity = '0';
    selectItems.style.transform = 'translateY(-10px)';
    selectSelected.classList.remove('select-arrow-active');
    isDropdownOpen = false;
    
    // 4. 選択ボタンのクリックイベント（シンプルに）
    selectSelected.addEventListener('click', (e) => {
        console.log('🎯 選択ボタンクリック');
        e.stopPropagation();
        toggleDropdown();
    });
    
    // 5. オプションクリックイベント（シンプルに）
    selectItems.addEventListener('click', (e) => {
        let clickedItem = e.target;
        while (clickedItem && !clickedItem.classList.contains('select-item')) {
            clickedItem = clickedItem.parentElement;
        }
        
        if (!clickedItem || !clickedItem.classList.contains('select-item')) {
            return;
        }
        
        const value = clickedItem.dataset.value;
        const isSeriesOption = clickedItem.classList.contains('series-option');
        
        console.log(`🎯 オプションクリック: ${value}`);
        
        // 選択処理を実行（非同期で）
        setTimeout(() => {
            this.handlePackSelection(value, isSeriesOption, clickedItem);
        }, 10);
        
        // ★★★ 重要：ここではドロップダウンを閉じない ★★★
        // ユーザーが複数選択できるようにする
    });
    
    // 6. ドキュメントクリックで閉じる（シンプルに）
    document.addEventListener('click', (e) => {
        if (!selectSelected.contains(e.target) && !selectItems.contains(e.target)) {
            if (isDropdownOpen) {
                toggleDropdown(false);
            }
        }
    });
    
    // 7. タブキーでも閉じる
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' && isDropdownOpen) {
            toggleDropdown(false);
        }
    });
    
    console.log('✅ setupPackSelectEventsDirectly() 完了 - シンプル実装');
}

handlePackSelection(value, isSeriesOption, clickedItem) {
    const selectItems = document.querySelector('.pack-selection-group .select-items');
    if (!selectItems) return;
    
    const isCurrentlySelected = clickedItem.classList.contains('selected');
    
    if (value === 'all') {
        // 「All Expansion Sets」ボタンの処理
        if (isCurrentlySelected) {
            // すでに選択されている場合は何もしない
            return;
        }
        
        // 全ての選択を解除して「All」を選択状態にする
        this.currentFilters.pack = [];
        
        // UIの選択状態をリセット
        selectItems.querySelectorAll('.select-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // 「All」ボタンのみ選択状態にする
        clickedItem.classList.add('selected');
        
    } else if (isSeriesOption) {
        // ★★★ シリーズ選択：対応する全パックをトグル ★★★
        const seriesData = this.packData[value];
        if (!seriesData || !seriesData.packs) return;
        
        if (isCurrentlySelected) {
            // シリーズの選択解除 → 対応する全パックを削除
            clickedItem.classList.remove('selected');
            
            seriesData.packs.forEach(packName => {
                const index = this.currentFilters.pack.indexOf(packName);
                if (index > -1) {
                    this.currentFilters.pack.splice(index, 1);
                }
                
                // 対応するパックボタンの選択も解除
                const packOption = selectItems.querySelector(`.pack-option[data-value="${packName}"]`);
                if (packOption) {
                    packOption.classList.remove('selected');
                }
            });
            
        } else {
            // シリーズの選択 → 対応する全パックを追加
            clickedItem.classList.add('selected');
            
            seriesData.packs.forEach(packName => {
                if (!this.currentFilters.pack.includes(packName)) {
                    this.currentFilters.pack.push(packName);
                }
                
                // 対応するパックボタンの選択も追加
                const packOption = selectItems.querySelector(`.pack-option[data-value="${packName}"]`);
                if (packOption) {
                    packOption.classList.add('selected');
                }
            });
        }
        
        // 「All」の選択状態を解除
        const allOption = selectItems.querySelector('.select-item[data-value="all"]');
        if (allOption) {
            allOption.classList.remove('selected');
        }
    } else {
        // 個別パック選択の処理
        if (isCurrentlySelected) {
            clickedItem.classList.remove('selected');
            const index = this.currentFilters.pack.indexOf(value);
            if (index > -1) {
                this.currentFilters.pack.splice(index, 1);
            }
        } else {
            clickedItem.classList.add('selected');
            if (!this.currentFilters.pack.includes(value)) {
                this.currentFilters.pack.push(value);
            }
        }
        
        // 「All」の選択状態を解除
        const allOption = selectItems.querySelector('.select-item[data-value="all"]');
        if (allOption) {
            allOption.classList.remove('selected');
        }
        
        // ★★★ シリーズの選択状態を更新 ★★★
        this.updateSeriesSelectionState(value);
    }
    
    // 表示を更新して検索を実行
    this.updateSelectedPacksDisplay();
    this.performFilteredSearch();
}

// 新しいメソッド: シリーズの選択状態を更新
updateSeriesSelectionState(changedPackName) {
    const selectItems = document.querySelector('.pack-selection-group .select-items');
    if (!selectItems || !this.packData) return;
    
    // 変更されたパックが属するシリーズを探す
    let targetSeriesKey = null;
    
    Object.keys(this.packData).forEach(seriesKey => {
        const seriesData = this.packData[seriesKey];
        if (seriesData.packs && seriesData.packs.includes(changedPackName)) {
            targetSeriesKey = seriesKey;
        }
    });
    
    if (!targetSeriesKey) return;
    
    const seriesOption = selectItems.querySelector(`.select-item.series-option[data-value="${targetSeriesKey}"]`);
    if (!seriesOption) return;
    
    const seriesData = this.packData[targetSeriesKey];
    if (!seriesData || !seriesData.packs) return;
    
    // このシリーズの全パックが選択されているかチェック
    const isAllPacksSelected = seriesData.packs.every(packName => 
        this.currentFilters.pack.includes(packName)
    );
    
    if (isAllPacksSelected) {
        seriesOption.classList.add('selected');
        console.log(`📊 シリーズ "${targetSeriesKey}" を全選択状態にしました`);
    } else {
        seriesOption.classList.remove('selected');
        console.log(`📊 シリーズ "${targetSeriesKey}" の全選択状態を解除しました`);
    }
}
// シリーズ選択状態を同期するメソッド
syncSeriesSelectionStates() {
    const selectItems = document.querySelector('.pack-selection-group .select-items');
    if (!selectItems) return;

    if (this.packData) {
        // 各シリーズの選択状態を更新
        Object.keys(this.packData).forEach(seriesName => {
            const seriesData = this.packData[seriesName];
            if (!seriesData.packs) return;
            
            const seriesOption = selectItems.querySelector(`.select-item.series-option[data-value="${seriesName}"]`);
            if (seriesOption) {
                // このシリーズの全パックが選択されているかチェック
                const isAllPacksSelected = seriesData.packs.every(pack => 
                    this.currentFilters.pack.includes(pack)
                );
                
                if (isAllPacksSelected) {
                    seriesOption.classList.add('selected');
                } else {
                    seriesOption.classList.remove('selected');
                }
            }
        });
    }
}

// 拡張パックフィルターをリセット
resetPackFilter() {
    console.log('🔄 resetPackFilter() 開始');
    
    // フィルター状態をリセット
    this.currentFilters.pack = [];
    
    // UIを更新
    const selectItems = document.querySelector('.pack-selection-group .select-items');
    if (selectItems) {
        // すべての選択を解除
        selectItems.querySelectorAll('.select-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // 「すべて」を選択状態にする
        const allOption = selectItems.querySelector('.select-item[data-value="all"]');
        if (allOption) {
            allOption.classList.add('selected');
        }
    }
    
    // 表示を更新
    this.updateSelectedPacksDisplay();
    
    // 検索を実行
    this.performFilteredSearch();
    console.log('✅ 拡張パックフィルターをリセットしました');
}

// 詳細フィルターをリセット
resetAdvancedFilters() {
    console.log('🔄 resetAdvancedFilters() 開始');
    
    // 詳細フィルターの状態をリセット
    this.currentFilters.type = [];
    this.currentFilters.rarity = [];
    this.currentFilters.hpMin = null;
    this.currentFilters.hpMax = null;
    this.currentFilters.damageMin = null;
    this.currentFilters.damageMax = null;
    this.currentFilters.other = [];
    this.currentFilters.trainer = [];
    
    // advancedFiltersコンテナ内のすべてのフィルターボタンのactiveクラスを削除
    const advancedFilters = document.getElementById('advancedFilters');
    if (advancedFilters) {
        // すべてのフィルターボタンのactiveクラスを削除
        advancedFilters.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    } else {
        // 代わりにすべてのフィルターボタンを対象にする
        document.querySelectorAll('.filter-btn[data-type="type"], .filter-btn[data-type="rarity"], .filter-btn[data-type="other"], .filter-btn[data-type="trainer"]').forEach(btn => {
            btn.classList.remove('active');
        });
    }
    
    // HPフィルターをリセット
    const hpMinSelect = document.getElementById('hpMin');
    const hpMaxSelect = document.getElementById('hpMax');
    if (hpMinSelect) hpMinSelect.value = '';
    if (hpMaxSelect) hpMaxSelect.value = '';
    this.syncHpOptions();
    
    // ーをリセット
    const damageMinSelect = document.getElementById('damageMin');
    const damageMaxSelect = document.getElementById('damageMax');
    if (damageMinSelect) damageMinSelect.value = '';
    if (damageMaxSelect) damageMaxSelect.value = '';
    this.syncDamageOptions();
    
    // 検索を実行
    this.performFilteredSearch();
}
  
applyPackFilter() {
    // Bulbasaurのデータを使ってテスト
    const bulbasaur = this.cardData.find(card => card['名前'] === 'Bulbasaur');
    if (bulbasaur) {
        console.log('   Bulbasaurのパック情報:', this.getCardPack(bulbasaur));
        console.log('   Bulbasaurがフィルターにマッチするか?:', this.checkPackFilter(bulbasaur));
    }
    
    this.performDebouncedSearch();

}


    // 拡張パック選択のイベント設定
    setupPackSelectEvents() {
        const selectSelected = document.querySelector('.pack-selection-group .select-selected');
        const selectItems = document.querySelector('.pack-selection-group .select-items');
    
        if (!selectSelected || !selectItems) {
            console.warn('拡張パック選択要素が見つかりません');
            return;
        }
    
        // 選択ボタンのクリックイベント
        selectSelected.addEventListener('click', (e) => {
            e.stopPropagation();

            selectItems.classList.toggle('show');
            selectSelected.classList.toggle('select-arrow-active');
            
            // 強制的に表示スタイルを適用
            if (selectItems.classList.contains('show')) {
                selectItems.style.display = 'block';
                selectItems.style.visibility = 'visible';
                selectItems.style.opacity = '1';
                selectItems.style.zIndex = '1000';
            } else {
                selectItems.style.display = 'none';
            }
        });
    
        // オプション要素のクリックイベントを直接設定
        const selectItemElements = selectItems.querySelectorAll('.select-item');
    
        selectItemElements.forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                
                const value = item.dataset.value;
                const text = item.querySelector('span').textContent;
                const iconElement = item.querySelector('img');
                const iconSrc = iconElement ? iconElement.src : '';
    
                // 選択状態を更新
                selectItemElements.forEach(i => {
                    i.classList.remove('selected');
                });
                item.classList.add('selected');
    
                // 表示を更新
                const selectedIcon = selectSelected.querySelector('img');
                const selectedText = selectSelected.querySelector('span');
                
                if (selectedIcon && iconSrc) {
                    selectedIcon.src = iconSrc;
                    selectedIcon.style.display = 'block';
                }
                if (selectedText) {
                    selectedText.textContent = text;
                }
    
                // フィルターを適用
                this.applyPackFilter(value);
    
                // ドロップダウンを閉じる
                selectItems.classList.remove('show');
                selectSelected.classList.remove('select-arrow-active');
                selectItems.style.display = 'none';
            });
        });
    
        // ドキュメントクリックイベントでドロップダウンを閉じる
        document.addEventListener('click', (e) => {
            if (!selectSelected.contains(e.target) && !selectItems.contains(e.target)) {
                selectItems.classList.remove('show');
                selectSelected.classList.remove('select-arrow-active');
                selectItems.style.display = 'none';
            }
        });
  }

    // 拡張パックフィルターを適用
    applyPackFilter(selectedValue) {
        if (selectedValue === 'all') {
            this.currentFilters.pack = [];
        } else {
            this.currentFilters.pack = [selectedValue];
        }
        this.performFilteredSearch();
    }
    
    // 検索結果数を表示するメソッドを修正 - 即時表示
    updateResultsCount(count, total) {
        let countElement = document.getElementById('resultsCount');
        
        if (!countElement) {
            countElement = document.createElement('div');
            countElement.id = 'resultsCount';
            countElement.className = 'results-count';
            
            // 検索結果コンテナの上に挿入
            const resultsContainer = document.getElementById('resultsContainer');
            if (resultsContainer) {
              resultsContainer.parentNode.insertBefore(countElement, resultsContainer);
            }
        }
        
        // 即時に表示（非同期処理を待たない）
        countElement.innerHTML = `
            <div class="results-count-text">
                  ${count} cards found${total ? ` / ${total} total cards` : ''}
            </div>
        `;
        
        // 即座に表示状態にする
        countElement.style.display = 'block';
        countElement.style.visibility = 'visible';
        countElement.style.opacity = '1';
}
    
async showAllCards() {
    // 詳細なスタックトレースを取得
    const stack = new Error().stack;
    
    // 呼び出し元を特定
    const callerLine = stack.split('\n')[2] || '不明';
    
    // もし handleSearch から呼ばれた場合は中止
    if (stack.includes('handleSearch')) {
        console.log('❌ handleSearch から呼ばれたので中止');
        return;
    }
    
    // 結果コンテナの現在の状態をチェック
    const resultsContainer = document.getElementById('resultsContainer');
    if (!resultsContainer) {
        console.log('⚠️ 結果コンテナが見つかりません');
        return;
    }
    
    // データがない場合は表示しない
    if (!this.cardData || this.cardData.length === 0) {
        return;
    }
    
    // ★★★ 即時クリア ★★★
    resultsContainer.innerHTML = '';
    
    const staticCards = document.getElementById('staticCards');
    
    if (staticCards) staticCards.style.display = 'none';

    // 検索結果数を即時表示
    this.updateResultsCount(this.cardData.length, this.cardData.length);
    
    // まずスケルトンを表示
    resultsContainer.style.display = 'grid';
    resultsContainer.innerHTML = Array(Math.min(this.cardData.length, 12)).fill(`
        <div class="card">
            <div class="card-image card-skeleton"></div>
        </div>
    `).join('');
    
    // 少し待ってから画像を読み込む（DOMの準備を待つ）
    setTimeout(async () => {
        const cardsHTML = await Promise.all(this.cardData.map(async (card, index) => {
            const imagePath = this.getCardImagePath(card);
            
            return new Promise((resolve) => {
                // 画像を事前にロードして状態を確認
                const testImg = new Image();
                
                testImg.onload = () => {
                    // 画像が正常に読み込めた場合
                    resolve(`
                        <a href="#" class="card">
                            <div class="card-image">
                                <img src="${imagePath}" alt="${card['名前']}" 
                                     class="card-img loaded" loading="lazy">
                            </div>
                        </a>
                    `);
                };
                
                testImg.onerror = () => {
                    // 画像読み込み失敗の場合、デフォルト画像を使用
                    console.warn(`⚠️ ${index + 1}/${this.cardData.length}: ${card['名前']} - 読み込み失敗 → デフォルト画像を使用`);
                    resolve(`
                        <a href="#" class="card">
                            <div class="card-image">
                                <img src="/images/cards/default.webp" alt="${card['名前']}" 
                                     class="card-img loaded" loading="lazy">
                            </div>
                        </a>
                    `);
                };
                
                // 画像の読み込みを開始（キャッシュ対策）
                testImg.src = imagePath + '?t=' + Date.now();
                
                // タイムアウト設定（3秒）
                setTimeout(() => {
                    if (!testImg.complete) {
                        console.warn(`⏰ ${index + 1}/${this.cardData.length}: ${card['名前']} - タイムアウト`);
                        testImg.src = '/images/cards/default.webp';
                    }
                }, 3000);
            });
        }));
        
        // 結果コンテナがまだ有効か確認（別の処理でクリアされていないか）
        const currentResultsContainer = document.getElementById('resultsContainer');
        if (!currentResultsContainer) {
            return;
        }
        
        // すべての画像HTMLが準備できたら表示を更新
        currentResultsContainer.innerHTML = cardsHTML.join('');
        
    }, 100); // 100ms待機してDOMの準備を確実にする
}

async showSearchResults(cards, searchId = null) {
    // ★★★ 無限スクロール用に結果を保存 ★★★
    this.currentSearchResults = cards;
    this.displayedCards = 0;
    this.hasMoreCards = cards.length > 0;
    
    // 最初のバッチのカードを表示
    await this.showFirstBatchOfResults(cards);
}

restoreFilterState() {
    const toggleButton = document.getElementById('toggleAdvancedFilters');
    const advancedFilters = document.getElementById('advancedFilters');
    
    if (toggleButton && advancedFilters) {
        // 初期状態は閉じた状態
        advancedFilters.style.display = 'none';
        toggleButton.classList.remove('active');
        
        const toggleText = toggleButton.querySelector('span:first-child');
        if (toggleText) {
            toggleText.textContent = 'Show Advanced Filters';
        }
    }
}

showLoadingState() {
    const resultsContainer = document.getElementById('resultsContainer');
    const staticCards = document.getElementById('staticCards');
    
    if (staticCards) staticCards.style.display = 'none';
    
    if (!resultsContainer) return;
    
    resultsContainer.style.display = 'grid';
    resultsContainer.innerHTML = `
        <div class="loading-indicator">
            <div class="spinner"></div>
            <p>Searching...</p>
        </div>
    `;
}

    getCardImagePath(card) {
        try {
            // キャッシュチェック
            const cacheKey = this.getImageCacheKey(card);
            if (this.failedImages.has(cacheKey)) {
                return this.getDefaultImagePath();
            }
            
            if (!card || typeof card !== 'object') {
                return this.getDefaultImagePath();
            }
            
            const cardName = card['名前'] || '不明なカード';
            let cardNumber = card['カード番号'];
            
            // 配列の場合の処理
            if (Array.isArray(cardNumber)) {
                if (cardNumber.length === 0) return this.getDefaultImagePath();
                cardNumber = cardNumber[0];
            }
            
            // 文字列でない場合
            if (!cardNumber || typeof cardNumber !== 'string') {
                return this.getDefaultImagePath();
            }
            
            // #形式のカード番号を処理
            if (cardNumber.includes('#')) {
                const [set, number] = cardNumber.split('#');
                if (set && number) {
                    const path = `/images/cards/${set}/${number}.webp`;
                    
                    // パス検証（オプション）
                    if (this.validateImagePath(path)) {
                        return path;
                    } else {
                        this.failedImages.add(cacheKey);
                    }
                }
            }
            
            return this.getDefaultImagePath();
            
        } catch (error) {
            return this.getDefaultImagePath();
        }
    }
    
    // キャッシュキー生成
    getImageCacheKey(card) {
        return JSON.stringify({
            name: card['名前'],
            number: card['カード番号']
        });
    }
    
    // 画像パスの事前検証（非同期）
    async validateImagePath(path) {
        return new Promise((resolve) => {
            const testImg = new Image();
            testImg.onload = () => resolve(true);
            testImg.onerror = () => resolve(false);
            testImg.src = path;
            
            // タイムアウト
            setTimeout(() => resolve(false), 2000);
        });
    }
    
    getDefaultImagePath() {
        return '/images/cards/default.webp';
    }

    clearResultsCount() {
    const countElement = document.getElementById('resultsCount');
    if (countElement) {
        countElement.style.display = 'none';
        countElement.innerHTML = '';
    }
}

    performDebouncedSearch() {
        // 既存のタイマーをクリア
        if (this.searchTimer) {
            clearTimeout(this.searchTimer);
        }
        
        // 新しいタイマーを設定
        this.searchTimer = setTimeout(() => {
            this.performFilteredSearch();
            this.searchTimer = null;
        }, this.debounceDelay);
}
    
resetFilters() {
    this.currentFilters = {
        type: [],
        cardType: [],
        rarity: [],
        hpMin: null,
        hpMax: null,
        other: [],
        trainer: [],
        damageMin: null,
        damageMax: null,
        pack: []
    };
    
    // すべてのボタンのactiveクラスを削除
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // カードの種類の「すべて」ボタンをアクティブに
    const allCardTypeButton = document.querySelector('.filter-btn[data-type="cardType"][data-value="all"]');
    if (allCardTypeButton) {
        allCardTypeButton.classList.add('active');
    }
    
    // HPフィルターもリセット
    this.resetHpFilter();
    
    // ワザーもリセット
    this.resetDamageFilter();
    
    // 拡張パックフィルターもリセット（複数選択対応版）
    this.resetPackFilter();
    
    // ★★★ 詳細フィルターの状態もリセット（オプション）★★★
    const advancedFilters = document.getElementById('advancedFilters');
    const toggleButton = document.getElementById('toggleAdvancedFilters');
    if (advancedFilters && toggleButton) {
        advancedFilters.style.display = 'none';
        toggleButton.classList.remove('active');
        toggleButton.querySelector('span:first-child').textContent = 'Show Advanced Filters';
    }
}
    
    waitForAllImages() {
        return new Promise((resolve) => {
            const images = document.querySelectorAll('#resultsContainer img');
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
                        if (loadedCount === images.length) {
                            resolve();
                        }
                    });
                    img.addEventListener('error', () => {
                        loadedCount++;
                        if (loadedCount === images.length) {
                            resolve();
                        }
                    });
                }
            });
            
            // 全て既に読み込み済みの場合
            if (loadedCount === images.length) {
                resolve();
            }
        });
    }
}

let currentSearchId = 0;

window.CardSearch = CardSearch;