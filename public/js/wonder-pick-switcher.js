/**
 * 汎用ワンダーピックスイッチャー
 * 使用方法:
 * 1. コンテナ要素に data-wp-switcher 属性を設定
 * 2. ボタンコンテナに data-wp-buttons 属性を設定
 * 3. コンテンツコンテナに data-wp-content 属性を設定
 * 4. パターンデータは data-wp-patterns 属性にJSON形式で設定
 * 
 * オプション:
 * - data-wp-default: デフォルトで表示するパターンID (デフォルト: "1")
 * - data-wp-type: "bonus" または "chansey" で画像クラスをカスタマイズ可能
 * - data-wp-show-cost: "true" の場合、コスト表示を追加
 */

(function() {
  // デフォルトの画像タイプに対応するCSSクラス名
  const DEFAULT_TYPE_CLASS_MAP = {
    ticket: 'bonus-pick-ticket',
    item: 'bonus-pick-item',
    card: 'bonus-pick-card'
  };

  // チャンシーピック用の画像クラス名（必要に応じてカスタマイズ）
  const CHANSEY_TYPE_CLASS_MAP = {
    ticket: 'chansey-pick-ticket',
    item: 'chansey-pick-item',
    card: 'chansey-pick-card'
  };

  // カードのリンク先マッピング（alt属性からパスを生成）
  function getCardLink(item) {
    // 1. itemにurlがあればそれを使う
    if (item.url) {
      // urlがスラッシュで終わっている場合は.htmlを追加
      let url = item.url;
      if (url.endsWith('/')) {
        url = url.slice(0, -1) + '.html';
      } else if (!url.endsWith('.html')) {
        url = url + '.html';
      }
      return url;
    }
    
    // 2. 通常カードはsrcまたはaltからパスを生成
    if (item.src && item.src.includes('/cards/')) {
      // src例: /images/cards/b2a/38.webp
      const pathMatch = item.src.match(/\/cards\/(.+?)\.webp$/);
      if (pathMatch) {
        const cardPath = pathMatch[1]; // b2a/38
        const parts = cardPath.split('/');
        const setId = parts[0]; // b2a
        const cardNumber = parts[1]; // 38
        
        // altからカード名を生成 (例: "Pawmi Common" -> "pawmi")
        let cardName = item.alt.toLowerCase();
        cardName = cardName.replace(/\s+common$/, '');
        cardName = cardName.replace(/\s+rare$/, '');
        cardName = cardName.replace(/\s+/g, '-');
        
        return `/cards/${setId}/${cardNumber}/${cardName}.html`;
      }
    }
    
    // 3. リンクがない場合は#を返す
    return '#';
  }

  /**
   * コスト表示のHTMLを生成
   * @returns {string} コスト表示のHTML
   */
  function renderCostDisplay() {
    return `
      <div class="cost_outer">
        <div class="cost_inner">
          <span class="cost_label">No cost</span>
        </div>
      </div>
    `;
  }

  /**
   * 単一アイテムのHTMLを生成
   * @param {Object} item - アイテムオブジェクト
   * @param {string} type - スイッチャーのタイプ
   * @returns {string} 生成されたHTML
   */
  function renderItem(item, type) {
    const typeClassMap = type === 'chansey' ? CHANSEY_TYPE_CLASS_MAP : DEFAULT_TYPE_CLASS_MAP;
    const imgClass = typeClassMap[item.type] || (type === 'chansey' ? 'chansey-pick-card' : 'bonus-pick-item');
    
    const imgTag = `<img src="${item.src}" alt="${item.alt}" class="${imgClass}">`;
    
    if (item.type === 'card') {
      const link = getCardLink(item);  // item全体を渡す
      if (link !== '#') {
        return `<a href="${link}" class="card-link">${imgTag}</a>`;
      }
    }
    
    return imgTag;
  }

  /**
   * パターンに基づいてHTMLを生成
   * @param {Object} pattern - パターンオブジェクト
   * @param {string} type - スイッチャーのタイプ ('bonus' または 'chansey')
   * @param {boolean} showCost - コスト表示を追加するかどうか
   * @returns {string} 生成されたHTML
   */
  function renderPatternGrid(pattern, type = 'bonus', showCost = false) {
    if (!pattern || !pattern.rows) return '';
  
    const rowsHtml = pattern.rows.map(row => {
      const rowInner = row.map(item => renderItem(item, type)).join('');
      return `<div class="cards-row">${rowInner}</div>`;
    }).join('');
  
    let html = `<div class="cards-grid">${rowsHtml}</div>`;
    
    // コスト表示を追加
    if (showCost) {
      // チャンシーピックの場合はWonder Stamina + 2を表示
      if (type === 'chansey') {
        html += `
          <div class="cost_outer">
            <div class="cost_inner">
              <img src="/images/items/Wonder Stamina.webp" alt="Wonder Stamina">
              <span class="cost_label">2</span>
            </div>
          </div>
        `;
      } else {
        // ボーナスピックの場合はNo costを表示
        html += renderCostDisplay();
      }
    }
    
    return html;
  }

  /**
   * スイッチャーを初期化
   * @param {HTMLElement} container - スイッチャーのコンテナ要素
   */
  function initSwitcher(container) {
    // 必要な要素を取得
    const buttonsContainer = container.querySelector('[data-wp-buttons]');
    const contentContainer = container.querySelector('[data-wp-content]');
    const patternsData = container.getAttribute('data-wp-patterns');
    const switcherType = container.getAttribute('data-wp-type') || 'bonus';
    // data-wp-show-cost が "true" の場合、または data-wp-type が "chansey" の場合は true
    const showCost = container.getAttribute('data-wp-show-cost') === 'true' || switcherType === 'chansey';

    if (!buttonsContainer || !contentContainer || !patternsData) {
      console.warn('Missing required attributes in switcher container');
      return;
    }

    // パターンデータをパース
    let patterns;
    try {
      patterns = JSON.parse(patternsData);
    } catch (e) {
      console.error('Invalid JSON in data-wp-patterns:', e);
      return;
    }

    // 初期表示
    const defaultPatternId = container.getAttribute('data-wp-default') || '1';
    if (patterns[defaultPatternId]) {
      contentContainer.innerHTML = renderPatternGrid(patterns[defaultPatternId], switcherType, showCost);
    }

    // ボタンのアクティブ状態を更新
    function updateActiveButton(activeButton) {
      const buttons = buttonsContainer.querySelectorAll('button');
      buttons.forEach(btn => btn.classList.remove('active'));
      activeButton.classList.add('active');
    }

    // イベントリスナー（イベントデリゲーション）
    buttonsContainer.addEventListener('click', (e) => {
      const button = e.target.closest('button');
      if (!button) return;

      const patternId = button.getAttribute('data-pattern');
      if (!patternId || !patterns[patternId]) return;

      // UI更新
      updateActiveButton(button);
      contentContainer.innerHTML = renderPatternGrid(patterns[patternId], switcherType, showCost);
    });
  }

  // すべてのスイッチャーを初期化
  function initAllSwitchers() {
    const switchers = document.querySelectorAll('[data-wp-switcher]');
    switchers.forEach(initSwitcher);
  }

  // DOM読み込み完了後に初期化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAllSwitchers);
  } else {
    initAllSwitchers();
  }
})();