// missions.js - 使い回し可能なミッション表示モジュール

// ========== 1. 設定 ==========
let RewardImages = {};

// ========== 2. ユーティリティ関数 ==========
const Utils = {
  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  },

  log(...args) {
    console.log('[Missions]', ...args);
  },

  error(...args) {
    console.error('[Missions]', ...args);
  }
};

// ========== 3. 設定読み込み関数 ==========
function loadConfigFromHTML() {
  const configScript = document.getElementById('missions-config');
  if (configScript) {
    try {
      const config = JSON.parse(configScript.textContent);
      if (config.rewardImages) {
        RewardImages = config.rewardImages;
        Utils.log('報酬画像マッピングを読み込みました:', RewardImages);
      }
    } catch (e) {
      Utils.error('設定の解析に失敗:', e);
    }
  }
}

// ========== 4. 報酬処理モジュール ==========
const RewardProcessor = {
  parseReward(rewardText) {
    if (!rewardText) return { itemName: '', quantity: 1 };
    
    // パターン1: "数量x アイテム名" (例: "1x Iono (profile icon)")
    const match1 = rewardText.match(/^(\d+)x\s+(.+)$/);
    if (match1) {
        return {
            itemName: match1[2].trim(),
            quantity: parseInt(match1[1], 10)
        };
    }
    
    // パターン2: "アイテム名 ×数量" (例: "Emblem Ticket ×10")
    const match2 = rewardText.match(/^(.+?)\s*×(\d+)$/);
    if (match2) {
        return {
            itemName: match2[1].trim(),
            quantity: parseInt(match2[2], 10)
        };
    }
    
    // パターン3: アイテム名のみ
    return { itemName: rewardText.trim(), quantity: 1 };
  },

  // アイテム名から画像パスを動的に生成（setsパラメータ追加）
  generateImagePath(itemName, sets = null) {
      console.log('generateImagePath called with:', JSON.stringify(itemName), 'sets:', sets);
      
      // ========== カード報酬の処理 ==========
      const cardMatch = itemName.match(/^(.+?)\s*\(#(\d+)\)$/);
      if (cardMatch) {
          const pokemonName = cardMatch[1].trim();
          const cardNumber = parseInt(cardMatch[2], 10);
          const setCode = sets || 'a2a';
          const result = `/images/cards/${setCode}/${cardNumber}.webp`;
          console.log('→ カード報酬検出:', result);
          return result;
      }
      
      // ========== プレイマット ==========
      if (itemName.includes('(playmat)')) {
          let cleanName = itemName.replace(' (playmat)', '').trim();
          let filename = cleanName.replace(/[:\s]/g, '_');
          filename = filename.replace(/_+/g, '_');
          const result = `/images/accessories/playmats/${filename}_playmat.webp`;
          console.log('→ プレイマット:', result);
          return result;
      }
      
      // ========== カードスリーブ ==========
      if (itemName.includes('(card sleeve)')) {
          let cleanName = itemName.replace(' (card sleeve)', '').trim();
          let filename = cleanName.replace(/[:\s]/g, '_');
          filename = filename.replace(/_+/g, '_');
          const result = `/images/accessories/card_sleeves/${filename}_card_sleeve.webp`;
          console.log('→ カードスリーブ:', result);
          return result;
      }
      
      // ========== ポケモンコイン ==========
      if (itemName.includes('(Pokémon coin)')) {
          let cleanName = itemName.replace(' (Pokémon coin)', '').trim();
          let filename = cleanName.replace(/[:\s]/g, '_');
          filename = filename.replace(/_+/g, '_');
          const result = `/images/accessories/coins/${filename}_Pokémon_coin.webp`;
          console.log('→ ポケモンコイン:', result);
          return result;
      }
      
      // エンブレムチケット
      if (itemName.includes('Emblem Ticket')) {
          const match = itemName.match(/Emblem Ticket \(([^)]+)\)/);
          if (match) {
              let series = match[1].replace(':', '_');
              return `/images/tickets/Emblem Ticket (${series}).webp`;
          }
          return '/images/tickets/Emblem Ticket (Deluxe Pack_ ex).webp';
      }
      
      // ショップチケット
      if (itemName.includes('Shop Ticket')) {
          return '/images/tickets/Shop ticket.webp';
      }
      
      // 砂時計類
      if (itemName.includes('Wonder Hourglass')) {
          return '/images/items/Wonder Hourglass.webp';
      }
      if (itemName.includes('Pack Hourglass')) {
          return '/images/items/Pack Hourglass.webp';
      }
      
      // プロフィールアイコン
      if (itemName.includes('(profile icon)')) {
          let cleanName = itemName.replace(' (profile icon)', '').trim();
          let filename = cleanName.replace(/[:\s]/g, '_');
          filename = filename.replace(/_+/g, '_');
          filename = filename + '_icon.webp';
          const result = `/images/accessories/icons/${filename}`;
          console.log('→ returns:', result);
          return result;
      }
      
      // エンブレム
      if (itemName.includes('(emblem)')) {
          const result = `/images/emblem/${itemName}.webp`;
          console.log('→ returns:', result);
          return result;
      }
      
      // カバーバインダー
      if (itemName.includes('(cover)')) {
          const filename = itemName.replace(/[:\s]/g, '_').replace('_(cover)', '_cover') + '.webp';
          const result = `/images/accessories/covers/${filename}`;
          console.log('→ returns:', result);
          return result;
      }
      
      // バックドロップ
      if (itemName.includes('(backdrop)')) {
          const cleanName = itemName.replace(' (backdrop)', '').trim();
          let filename = cleanName.replace(/[:\s]/g, '_');
          filename = filename.replace(/_+/g, '_');
          filename = filename + '_backdrop.webp';
          const result = `/images/accessories/backdrops/${filename}`;
          console.log('→ returns:', result);
          return result;
      }
      
      const result = '/images/placeholder.webp';
      console.log('→ returns (placeholder):', result);
      return result;
  },

  getImagePath(itemName, sets = null) {
    // まず既存のマッピングをチェック
    if (RewardImages[itemName]) {
      return RewardImages[itemName];
    }
    
    // 動的に生成（setsを渡す）
    return this.generateImagePath(itemName, sets);
  },
  
  generateRewardItemHtml(rewardText, sets = null) {
      const { itemName, quantity } = this.parseReward(rewardText);
      const imagePath = this.getImagePath(itemName, sets);
      
      if (!itemName) return '';
      
      // カード報酬かどうかチェック
      const cardMatch = itemName.match(/^(.+?)\s*\(#(\d+)\)$/);
      const isCard = !!cardMatch;
      
      // リンクURLを生成（カードの場合のみ）
      let linkUrl = '';
      if (isCard) {
          const pokemonName = cardMatch[1].trim();
          const cardNumber = cardMatch[2];
          const setCode = sets || 'a2a';
          linkUrl = `/cards/${setCode}/${parseInt(cardNumber, 10)}/${pokemonName}.html`;
      }
      
      // 画像部分（カードの場合はリンク付き）
      const imageHtml = isCard
          ? `<a href="${linkUrl}" class="card-link"><img src="${imagePath}" alt="${Utils.escapeHtml(itemName)}" onerror="this.src='/images/placeholder.webp'"></a>`
          : `<img src="${imagePath}" alt="${Utils.escapeHtml(itemName)}" onerror="this.src='/images/placeholder.webp'">`;
      
      return `
          <div class="mission-card__preview-item tooltip">
              ${imageHtml}
              <span>×${quantity}</span>
              <span class="tooltiptext">${Utils.escapeHtml(itemName)}</span>
          </div>
      `;
  },

  generateRewardsHtml(rewardTexts, sets = null) {
    if (!rewardTexts) return '';
    
    let itemsHtml = '';
    if (Array.isArray(rewardTexts)) {
      itemsHtml = rewardTexts.map(text => this.generateRewardItemHtml(text, sets)).join('');
    } else {
      itemsHtml = this.generateRewardItemHtml(rewardTexts, sets);
    }
    
    return `<div class="mission-card__preview">${itemsHtml}</div>`;
  }
};

// ========== 5. 図鑑ミッション表示モジュール ==========
const DexMissionRenderer = {
  getSecretBadge(secret) {
    return secret ? '<span class="secret-badge">Secret</span>' : '';
  },

  createMissionCard(mission) {
    const rewardsHtml = RewardProcessor.generateRewardsHtml(mission.reward);
    const secretBadge = this.getSecretBadge(mission.secret);

    const card = document.createElement('div');
    card.className = 'mission-card';
    card.innerHTML = `
      <div class="mission-card__inner">
        ${rewardsHtml}
        <div class="mission-card__content">
          <div class="mission-card__text">
            ${Utils.escapeHtml(mission.mission)}${secretBadge}
          </div>
        </div>
      </div>
    `;
    return card;
  },

  renderNormal(container, missions) {
    if (!missions || missions.length === 0) return false;

    const missionList = document.createElement('div');
    missionList.className = 'mission-list';

    missions.forEach(mission => {
      missionList.appendChild(this.createMissionCard(mission));
    });

    container.appendChild(missionList);
    return true;
  },

  renderSecret(container, secretMissions) {
    if (!secretMissions || secretMissions.length === 0) return false;

    const secretHeader = document.createElement('div');
    secretHeader.className = 'secret-header';
    secretHeader.innerHTML = '<h4>Secret Missions</h4>';
    container.appendChild(secretHeader);

    const missionList = document.createElement('div');
    missionList.className = 'mission-list';

    secretMissions.forEach(mission => {
      missionList.appendChild(this.createMissionCard(mission));
    });

    container.appendChild(missionList);
    return true;
  },

  render(container, missions) {
    container.innerHTML = '';
    
    const normalMissions = missions.filter(m => !m.secret);
    const secretMissions = missions.filter(m => m.secret);
    
    this.renderNormal(container, normalMissions);
    this.renderSecret(container, secretMissions);
    
    if (normalMissions.length === 0 && secretMissions.length === 0) {
      container.innerHTML = '<div class="loading">No missions found.</div>';
    }
  }
};

// ========== 6. テーマコレクション表示モジュール（修正版） ==========
const CollectionRenderer = {
  getSecretBadge(secret) {
    return secret ? '<span class="secret-badge">Secret</span>' : '';
  },

  createCollectionCard(collection) {
    let rewardTexts = [];
    
    if (Array.isArray(collection.reward)) {
      // Dex Missions と同じ形式に変換（「数量x アイテム名」）
      rewardTexts = collection.reward.map(reward => `${reward.quantity}x ${reward.item}`);
    } else if (typeof collection.reward === 'string') {
      rewardTexts = [collection.reward];
    } else if (collection.reward && collection.reward.item) {
      rewardTexts = [`${collection.reward.quantity}x ${collection.reward.item}`];
    }
    
    // sets情報を取得（なければnull）
    const sets = collection.sets || null;
    const rewardsHtml = RewardProcessor.generateRewardsHtml(rewardTexts, sets);
    const secretBadge = this.getSecretBadge(collection.secret);

    const card = document.createElement('div');
    card.className = 'mission-card';
    card.innerHTML = `
      <div class="mission-card__inner">
        ${rewardsHtml}
        <div class="mission-card__content">
          <div class="mission-card__text">
            ${Utils.escapeHtml(collection.name)}${secretBadge}
          </div>
        </div>
      </div>
    `;
    return card;
  },

  renderNormal(container, collections) {
    if (!collections || collections.length === 0) return false;

    const collectionList = document.createElement('div');
    collectionList.className = 'mission-list';

    collections.forEach(collection => {
      collectionList.appendChild(this.createCollectionCard(collection));
    });

    container.appendChild(collectionList);
    return true;
  },

  renderSecret(container, secretCollections) {
    if (!secretCollections || secretCollections.length === 0) return false;

    const secretHeader = document.createElement('div');
    secretHeader.className = 'secret-header';
    secretHeader.innerHTML = '<h4>Secret Missions</h4>';
    container.appendChild(secretHeader);

    const collectionList = document.createElement('div');
    collectionList.className = 'mission-list';

    secretCollections.forEach(collection => {
      collectionList.appendChild(this.createCollectionCard(collection));
    });

    container.appendChild(collectionList);
    return true;
  },

  render(container, collections, secretCollections = []) {
    container.innerHTML = '';
    
    this.renderNormal(container, collections);
    this.renderSecret(container, secretCollections);
    
    if (collections.length === 0 && secretCollections.length === 0) {
      container.innerHTML = '<div class="loading">No collections found.</div>';
    }
  }
};

// ========== 7. データ読み込みモジュール ==========
const DataLoader = {
  async loadJSON(path) {
    try {
      Utils.log(`JSON読み込み: ${path}`);
      
      const response = await fetch(path, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      Utils.error('JSON読み込み失敗:', error);
      throw error;
    }
  },

  showError(container, error, path) {
    container.innerHTML = `
      <div class="error" style="text-align:center;padding:2rem;color:#d32f2f;background:#ffebee;border-radius:8px;margin:1rem 0;">
        <strong>⚠️ データの読み込みに失敗しました</strong><br>
        ${Utils.escapeHtml(error.message)}<br>
        <small>パス: ${path}</small>
      </div>
    `;
  },

  showLoading(container, message) {
    container.innerHTML = `<div class="loading" style="text-align:center;padding:2rem;">${message}</div>`;
  }
};

// ========== 8. リトライ機能 ==========
async function loadWithRetry(loader, maxRetries = 3, delay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      Utils.log(`読み込み試行 ${i + 1}/${maxRetries}`);
      return await loader();
    } catch (error) {
      Utils.log(`リトライ ${i + 1}/${maxRetries} 失敗`);
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

// ========== 9. ツールチップ再初期化関数 ==========
function reinitTooltips() {
  // tooltip.js の初期化関数があれば呼び出す
  if (typeof initTooltips === 'function') {
    initTooltips();
  } else {
    // または、動的要素にクリックイベントを再適用
    const tooltips = document.querySelectorAll('.tooltip');
    tooltips.forEach(tooltip => {
      if (tooltip.hasAttribute('data-tooltip-initialized')) return;
      tooltip.setAttribute('data-tooltip-initialized', 'true');
      
      tooltip.addEventListener('click', function(e) {
        e.stopPropagation();
        
        const tooltipText = this.querySelector('.tooltiptext');
        if (!tooltipText) return;
        
        const isActive = this.classList.contains('is-active');
        
        // 他のツールチップをすべてリセット
        document.querySelectorAll('.tooltip').forEach(t => {
          t.classList.remove('is-active');
          t.classList.remove('is-bottom');
          const text = t.querySelector('.tooltiptext');
          if (text) text.style.setProperty('--offset', '0px');
        });
        
        if (!isActive) {
          this.classList.add('is-active');
          
          // 左右のはみ出し補正
          const rect = tooltipText.getBoundingClientRect();
          const padding = 15;
          const screenWidth = window.innerWidth;
          
          let offset = 0;
          if (rect.left < padding) {
            offset = padding - rect.left;
          } else if (rect.right > screenWidth - padding) {
            offset = (screenWidth - padding) - rect.right;
          }
          tooltipText.style.setProperty('--offset', `${offset}px`);
          
          // 上下のはみ出し補正
          const updatedRect = tooltipText.getBoundingClientRect();
          if (updatedRect.top < 0) {
            this.classList.add('is-bottom');
          }
        }
      });
    });
  }
}

// ========== 10. メイン関数 ==========
async function loadMissions() {
  loadConfigFromHTML();
  
  const dexContainer = document.getElementById('mission-container');
  const collectionsContainer = document.getElementById('themed-collections-container');
  
  if (dexContainer) {
    const dexPath = dexContainer.dataset.dexPath;
    if (dexPath) {
      DataLoader.showLoading(dexContainer, '図鑑ミッションを読み込み中...');
      try {
        const data = await loadWithRetry(() => DataLoader.loadJSON(dexPath));
        if (data.missions) {
          DexMissionRenderer.render(dexContainer, data.missions);
        }
      } catch (error) {
        DataLoader.showError(dexContainer, error, dexPath);
      }
    } else {
      Utils.error('mission-containerにdata-dex-pathが指定されていません');
    }
  }
  
  if (collectionsContainer) {
    const collectionsPath = collectionsContainer.dataset.collectionsPath;
    if (collectionsPath) {
      DataLoader.showLoading(collectionsContainer, 'テーマコレクションを読み込み中...');
      try {
        const data = await loadWithRetry(() => DataLoader.loadJSON(collectionsPath));
        const collections = data.collections || [];
        const secretMissions = data.secret_missions || [];
        CollectionRenderer.render(collectionsContainer, collections, secretMissions);
      } catch (error) {
        DataLoader.showError(collectionsContainer, error, collectionsPath);
      }
    } else {
      Utils.error('themed-collections-containerにdata-collections-pathが指定されていません');
    }
  }
  
  // ミッション読み込み後にツールチップを再初期化
  reinitTooltips();
}

// ========== 11. 実行 ==========
document.addEventListener('DOMContentLoaded', loadMissions);