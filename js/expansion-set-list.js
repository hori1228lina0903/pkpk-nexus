// expansion-set-list.js
document.addEventListener('DOMContentLoaded', function() {
  console.log('expansion-set-list.js loaded');
  
  const jsonPath = '/data/pack_set_name.json';
  
  fetch(jsonPath)
    .then(response => response.json())
    .then(data => {
      console.log('Loaded expansion sets:', Object.keys(data).length);
      
      // シリーズごとに分類
      const seriesA = [];
      const seriesB = [];
      
      Object.keys(data).forEach(key => {
        const setData = data[key];
        setData.code = key;
        
        if (key === 'Promo') {
          // Promo を個別に分割
          setData.packs.forEach(pack => {
            const promoItem = {
              ...setData,
              set: pack,
              packs: [pack]
            };
            if (pack === 'Promo A') {
              seriesA.push(promoItem);
            } else if (pack === 'Promo B') {
              seriesB.push(promoItem);
            }
          });
        } else if (key.startsWith('a')) {
          seriesA.push(setData);
        } else if (key.startsWith('b')) {
          seriesB.push(setData);
        }
      });
      
      // コード順にソート
      seriesA.sort((a, b) => a.code.localeCompare(b.code));
      seriesB.sort((a, b) => a.code.localeCompare(b.code));
      
      // データを保存
      window.seriesData = { seriesA, seriesB };
      
      // デフォルトでAシリーズを表示
      showSeries('A');
      
      // タブボタンのイベントリスナー
      const buttons = document.querySelectorAll('.tab-btn');
      buttons.forEach(btn => {
        btn.addEventListener('click', function() {
          buttons.forEach(b => b.classList.remove('active'));
          this.classList.add('active');
          showSeries(this.dataset.series);
        });
      });
    })
    .catch(error => {
      console.error('Failed to load expansion sets:', error);
      const expansionContainer = document.querySelector('.expansion-container');
      if (expansionContainer) {
        expansionContainer.innerHTML = '<p>Failed to load expansion sets.</p>';
      }
    });
});

// セットコードのフォーマット（A2A → A2a）
function formatSetCode(code) {
  const upperCode = code.toUpperCase();
  return upperCode.replace(/^([A-Z])(\d+)([A-Z])$/, (match, series, num, letter) => {
    return series + num + letter.toLowerCase();
  });
}

function showSeries(series) {
  const expansionContainer = document.querySelector('.expansion-container');
  if (!expansionContainer) return;
  
  let seriesData = series === 'A' ? window.seriesData.seriesA : window.seriesData.seriesB;
  
  if (!seriesData || seriesData.length === 0) {
    expansionContainer.innerHTML = '<p>No expansion sets available.</p>';
    return;
  }
  
  let html = '<div class="expansion-grid">';
  
  seriesData.forEach(set => {
    const imagePath = `/images/packs/${set.set}.webp`;
    let linkPath = '';
    
    // Promo かどうかでリンク先を変更
    if (set.set === 'Promo A' || set.set === 'Promo B') {
      linkPath = `/sets/Promo/${set.set}.html`;
    } else {
      linkPath = `/sets/${set.code}/${set.set}.html`;
    }
    
    html += `
      <a href="${linkPath}" class="expansion-card">
        <div class="expansion-card-inner">
          <img src="${imagePath}" alt="${set.set}" class="expansion-image" 
               onerror="this.src='/images/packs/default.webp'">
          <div class="expansion-info">
            <div class="expansion-name">${set.set}</div>
            <div class="expansion-code">${formatSetCode(set.code)}</div>
          </div>
        </div>
      </a>
    `;
  });
  
  html += '</div>';
  expansionContainer.innerHTML = html;
}