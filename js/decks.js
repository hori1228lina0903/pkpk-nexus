// decks.js
document.addEventListener('DOMContentLoaded', function() {
  console.log('decks.js loaded');
  
  // 最新のexpansionを取得して説明文を更新
  updateLatestExpansionText();
  
  const jsonPath = '/data/decks.json';
  
  fetch(jsonPath)
    .then(response => response.json())
    .then(data => {
      console.log('Loaded decks:', data);
      
      // New Pack Decks を表示
      if (data.new && data.new.length > 0) {
        renderDecks('.new-deck-grid', data.new);
      }
      
      // Tier Decks を表示（S, A, B, C, D）
      const tiers = ['S', 'A', 'B', 'C', 'D'];
      tiers.forEach(tier => {
        if (data[tier] && data[tier].length > 0) {
          renderDecks(`.tier-${tier.toLowerCase()}-grid`, data[tier]);
        }
      });
    })
    .catch(error => {
      console.error('Failed to load decks:', error);
    });
});

function renderDecks(selector, decks) {
  const container = document.querySelector(selector);
  if (!container) return;
  
  let html = '';
  decks.forEach(deck => {
    html += `
      <a class="content-link" href="${deck.link}">
        <div class="deck-container">
          <img src="${deck.image}" alt="${deck.name}">
          <div class="overlay-text">${deck.name}</div>
        </div>
      </a>
    `;
  });
  container.innerHTML = html;
}

// 最新のexpansionを取得して説明文を更新する関数
function updateLatestExpansionText() {
  const packSetPath = '/data/pack_set_name.json';
  
  function getLatestExpansion(packData) {
    const filtered = Object.keys(packData)
      .filter(key => key !== 'Promo')
      .map(key => ({ key, ...packData[key] }));
    
    function compareVersion(a, b) {
      const parse = (str) => {
        const match = str.match(/^([a-z])(\d+)([a-z]?)$/i);
        if (!match) return { major: 0, minor: 0, sub: '' };
        return {
          major: match[1].toLowerCase(),
          minor: parseInt(match[2], 10),
          sub: match[3] || ''
        };
      };
      
      const aParsed = parse(a);
      const bParsed = parse(b);
      
      if (aParsed.major !== bParsed.major) {
        return aParsed.major > bParsed.major ? 1 : -1;
      }
      if (aParsed.minor !== bParsed.minor) {
        return aParsed.minor - bParsed.minor;
      }
      const aSub = aParsed.sub || '';
      const bSub = bParsed.sub || '';
      if (aSub !== bSub) {
        if (aSub === '') return -1;
        if (bSub === '') return 1;
        return aSub.localeCompare(bSub);
      }
      return 0;
    }
    
    const sorted = filtered.sort((x, y) => compareVersion(y.key, x.key));
    return sorted[0] || null;
  }
  
  fetch(packSetPath)
    .then(response => response.json())
    .then(packData => {
      const latest = getLatestExpansion(packData);
      if (latest) {
        const expansionName = latest.set;
        // getElementById を使用
        const expansionTextElement = document.getElementById('latest-expansion-text');
        if (expansionTextElement) {
          expansionTextElement.innerHTML = `Featuring new decks from the latest expansion, ${expansionName}.`;
          console.log(`Updated expansion text to: ${expansionName}`);
        } else {
          console.warn('Element with id "latest-expansion-text" not found');
        }
      }
    })
    .catch(error => {
      console.error('Failed to load pack_set_name.json:', error);
    });
}