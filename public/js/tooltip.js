// tooltip.js
function initTooltips() {
  const tooltips = document.querySelectorAll('.tooltip');
  
  tooltips.forEach(tooltip => {
    // 二重登録防止
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

// 初期化
initTooltips();

// 動的な要素の追加に対応（必要に応じて）
const observer = new MutationObserver(() => initTooltips());
observer.observe(document.body, { childList: true, subtree: true });